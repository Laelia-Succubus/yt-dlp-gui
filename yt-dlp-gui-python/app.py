import os
import json
import uuid
import threading
import subprocess
import re
from bottle import route, run, template, request, response, static_file, abort

DOWNLOADS_DIR = '/app/downloads'
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

downloads = {}
download_locks = {}

def get_video_info(url):
    cmd = ['yt-dlp', '--dump-json', '--no-download', '--quiet', '--force-ipv4', '--no-check-certificate', '--write-subs', '--write-auto-subs', url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        stdout = result.stdout.strip()
        
        if result.returncode != 0:
            stderr = result.stderr.strip() if result.stderr else ""
            return {'error': stderr[:200] if stderr else 'Download failed'}
        
        if not stdout:
            return {'error': 'No output from yt-dlp'}
        
        json_lines = [l for l in stdout.split('\n') if l.strip().startswith('{')]
        
        if not json_lines:
            return {'error': 'No video data found in output'}
        
        try:
            data = json.loads(json_lines[0])
        except json.JSONDecodeError as e:
            return {'error': f'Failed to parse video data: {str(e)}'}
        
        formats = []
        if data.get('formats'):
            for f in data['formats']:
                formats.append({
                    'format_id': f.get('format_id', ''),
                    'ext': f.get('ext', ''),
                    'resolution': f.get('resolution', ''),
                    'fps': f.get('fps', ''),
                    'vcodec': f.get('vcodec', ''),
                    'acodec': f.get('acodec', ''),
                    'filesize': f.get('filesize', 0) or f.get('filesize_approx', 0)
                })
        
        chapters = []
        if data.get('chapters'):
            for ch in data['chapters']:
                chapters.append({
                    'title': ch.get('title', ''),
                    'start_time': ch.get('start_time', 0),
                    'end_time': ch.get('end_time', 0)
                })
        
        subtitles = data.get('subtitles') or {}
        
        return {
            'title': data.get('title', 'Unknown'),
            'thumbnail': data.get('thumbnail', ''),
            'duration': data.get('duration', 0),
            'description': data.get('description', '')[:500],
            'is_live': data.get('is_live', False),
            'view_count': data.get('view_count', 0),
            'channel': data.get('uploader', ''),
            'formats': formats,
            'chapters': chapters,
            'subtitles': subtitles
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Request timed out'}
    except Exception as e:
        return {'error': str(e)}

def download_video(download_id, url, options):
    try:
        downloads[download_id]['status'] = 'downloading'
        
        safe_title = "".join(c for c in options.get('title', 'video') if c.isalnum() or c in ' -_').strip()[:50]
        filename = f"{safe_title}.%(ext)s"
        
        cmd = ['yt-dlp', '-f', options.get('format_id', 'best')]
        
        if options.get('save_path'):
            cmd.extend(['-o', os.path.join(options['save_path'], filename)])
        else:
            cmd.extend(['-o', os.path.join(DOWNLOADS_DIR, filename)])
        
        if options.get('embed_thumbnail'):
            cmd.append('--embed-thumbnail')
        if options.get('embed_chapters'):
            cmd.append('--embed-chapters')
        if options.get('embed_subtitles'):
            cmd.extend(['--embed-subs'])
        
        if options.get('time_range'):
            cmd.extend(['--download-sections', options['time_range']])
        
        if options.get('rate_limit'):
            cmd.extend(['--limit-rate', options['rate_limit']])
        
        if options.get('proxy'):
            cmd.extend(['--proxy', options['proxy']])
        
        if options.get('chapter'):
            try:
                ch_idx = int(options['chapter'])
                if options.get('chapters'):
                    ch = options['chapters'][ch_idx]
                    cmd.extend(['--download-sections', f'{ch["start_time"]}-{ch["end_time"]}'])
            except:
                pass
        
        if options.get('subtitle'):
            cmd.extend(['--sub-lang', options['subtitle']])
            cmd.append('--write-subs')
            cmd.extend(['--convert-subs', 'srt'])
        
        cmd.append(url)
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        download_locks[download_id] = process
        
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            downloads[download_id]['status'] = 'completed'
            downloads[download_id]['progress'] = 100
            
            output_file = stderr.decode() if stderr else ''
            match = re.search(r'\[download\] Destination: (.+)', output_file)
            if match:
                filepath = match.group(1).strip()
                if os.path.exists(filepath):
                    downloads[download_id]['filepath'] = filepath
        else:
            downloads[download_id]['status'] = 'failed'
            downloads[download_id]['error'] = stderr.decode()[:200] if stderr else 'Unknown error'
    except Exception as e:
        downloads[download_id]['status'] = 'failed'
        downloads[download_id]['error'] = str(e)
    finally:
        if download_id in download_locks:
            del download_locks[download_id]

@route('/')
def home():
    return static_file('index.html', root='/app')

@route('/static/<filepath:path>')
def static(filepath):
    return static_file(filepath, root='/app/static')

@route('/api/info', method='POST')
def api_info():
    data = request.json
    url = data.get('url')
    if not url:
        return {'error': 'No URL provided'}
    return get_video_info(url)

@route('/api/download', method='POST')
def api_download():
    data = request.json
    url = data.get('url')
    format_id = data.get('format_id', 'best')
    
    if not url:
        return {'error': 'No URL provided'}
    
    download_id = str(uuid.uuid4())
    info = get_video_info(url)
    title = info.get('title', 'video')
    
    downloads[download_id] = {
        'id': download_id,
        'url': url,
        'format_id': format_id,
        'title': title,
        'status': 'queued',
        'progress': 0,
        'chapters': info.get('chapters', []),
        'options': data
    }
    
    thread = threading.Thread(target=download_video, args=(download_id, url, {
        'format_id': format_id,
        'title': title,
        'save_path': data.get('save_path', ''),
        'embed_thumbnail': data.get('embed_thumbnail', True),
        'embed_chapters': data.get('embed_chapters', True),
        'embed_subtitles': data.get('embed_subtitles', False),
        'time_range': data.get('time_range', ''),
        'rate_limit': data.get('rate_limit', ''),
        'proxy': data.get('proxy', ''),
        'chapter': data.get('chapter', ''),
        'chapters': info.get('chapters', []),
        'subtitle': data.get('subtitle', '')
    }))
    thread.start()
    
    return {'id': download_id, 'status': 'queued', 'title': title}

@route('/api/status/<download_id>')
def api_status(download_id):
    if download_id not in downloads:
        return {'error': 'Download not found'}
    return downloads[download_id]

@route('/api/list')
def api_list():
    return {'downloads': list(downloads.values())}

@route('/api/cancel/<download_id>', method='POST')
def api_cancel(download_id):
    if download_id in download_locks:
        download_locks[download_id].terminate()
        downloads[download_id]['status'] = 'cancelled'
        del download_locks[download_id]
        return {'status': 'cancelled'}
    return {'error': 'Download not found or already completed'}


@route('/api/delete/<download_id>', method='DELETE')
def api_delete(download_id):
    if download_id in downloads:
        if download_id in download_locks:
            download_locks[download_id].terminate()
            del download_locks[download_id]
        filepath = downloads[download_id].get('filepath')
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        del downloads[download_id]
        return {'status': 'deleted'}
    return {'error': 'Download not found'}

@route('/api/files')
def api_files():
    files = []
    for f in os.listdir(DOWNLOADS_DIR):
        filepath = os.path.join(DOWNLOADS_DIR, f)
        if os.path.isfile(filepath):
            size = os.path.getsize(filepath)
            files.append({'name': f, 'size': size, 'path': f})
    return {'files': files}

@route('/api/file/<filepath:path>')
def api_download_file(filepath):
    path = os.path.join(DOWNLOADS_DIR, filepath)
    if os.path.exists(path):
        return static_file(filepath, root=DOWNLOADS_DIR, download=True)
    abort(404, 'File not found')

if __name__ == "__main__":
    run(host='0.0.0.0', port=8080)
