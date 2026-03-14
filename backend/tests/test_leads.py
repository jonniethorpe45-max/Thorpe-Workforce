import json


def test_lead_import(client, auth_headers):
    rows = [
        {"company_name": "Acme", "email": "a@acme.com", "full_name": "A Lead", "title": "VP Sales"},
        {"company_name": "Acme", "email": "a@acme.com", "full_name": "A Lead", "title": "VP Sales"},
        {"company_name": "Beta", "email": "b@beta.com", "full_name": "B Lead", "title": "Head of Growth"},
    ]
    res = client.post("/leads/import", headers=auth_headers, data={"json_rows": json.dumps(rows)})
    assert res.status_code == 200
    assert res.json()["created"] == 2
    assert res.json()["skipped_duplicates"] == 1
