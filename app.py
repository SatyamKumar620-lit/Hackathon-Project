from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from database import *
from scraper import enrich_company
import json

app = FastAPI(title="Prospect Research Agent")

templates = Jinja2Templates(directory="templates")


# Request Schema
class UrlRequest(BaseModel):
    url: str


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.post("/enrich")
def enrich(payload: UrlRequest):

    try:

        result = enrich_company(payload.url)

        conn = engine.connect()

        conn.execute(
            companies.insert().values(
                website_name=result.get("website_name", ""),
                company_name=result.get("company_name", ""),
                address=result.get("address", ""),
                mobile_number=result.get("mobile_number", ""),
                mail=json.dumps(result.get("mail", [])),
                core_service=result.get("core_service", ""),
                target_customer=result.get("target_customer", ""),
                probable_pain_point=result.get("probable_pain_point", ""),
                outreach_opener=result.get("outreach_opener", "")
            )
        )

        conn.commit()
        conn.close()

        return result

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/results")
def results():

    conn = engine.connect()

    rows = conn.execute(
        companies.select()
    ).fetchall()

    conn.close()

    output = []

    for row in rows:

        output.append({
            "website_name": row.website_name,
            "company_name": row.company_name,
            "address": row.address,
            "mobile_number": row.mobile_number,
            "mail": json.loads(row.mail) if row.mail else [],
            "core_service": row.core_service,
            "target_customer": row.target_customer,
            "probable_pain_point": row.probable_pain_point,
            "outreach_opener": row.outreach_opener
        })

    return output