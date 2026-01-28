## Download Script Approach

import requests
from datetime import datetime


def download_ratings(short_url, password):
    session = requests.Session()

    # 1. Follow redirect to get UUID
    resp = session.get(short_url, allow_redirects=True)
    uuid = resp.url.split('/links/')[-1].split('?')[0]

    # 2. Construct direct download URL
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"Digi 24-audiente zilnice {today}.xlsx"

    download_url = (
        f"https://storage.rcs-rds.ro/content/links/{uuid}/files/get/"
        f"{requests.utils.quote(filename)}"
        f"?path=%2F{requests.utils.quote(filename)}&password={password}"
    )

    # 3. Download
    resp = session.get(download_url)
    if resp.status_code == 200:
        return resp.content
    return None


