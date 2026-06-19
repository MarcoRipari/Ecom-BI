import base64
import requests

def upload_file_to_github(token: str, repo: str, file_path: str, new_content_bytes: bytes, commit_message: str) -> bool:
    """Carica un file su GitHub usando le REST API (sovrascrive se esiste)."""
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 1. Ottieni lo SHA se il file esiste
    response = requests.get(url, headers=headers)
    sha = None
    if response.status_code == 200:
        sha = response.json()['sha']
        
    encoded_content = base64.b64encode(new_content_bytes).decode("utf-8")
    
    # 2. Effettua il commit
    payload = {
        "message": commit_message,
        "content": encoded_content,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
        
    put_response = requests.put(url, headers=headers, json=payload)
    return put_response.status_code in [200, 201]

def trigger_github_workflow(token: str, repo: str, workflow_name: str = "daily_etl.yml") -> bool:
    """Avvia forzatamente una GitHub Action via API."""
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_name}/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {"ref": "main"}
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code == 204

def get_workflow_runs(token: str, repo: str) -> list:
    """Recupera le ultime esecuzioni della pipeline."""
    url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=8"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('workflow_runs', [])
    return []
