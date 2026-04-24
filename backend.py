from fastapi import FastAPI
from pydantic import BaseModel
from playwright.sync_api import sync_playwright

app = FastAPI()

class Req(BaseModel):
    pinfl: str

@app.post("/check")
def check(data: Req):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://aileaders.uz/auth/login/check")

        # PINFL input (2-chi input)
        inputs = page.locator("input")
        inputs.nth(1).fill(data.pinfl)

        # Tekshirish tugmasi
        page.locator("button").filter(has_text="Tekshirish").click()

        # natija chiqishini kutish
        page.wait_for_timeout(2000)

        body = page.inner_text("body")

        email = ""
        courses = "0"

        if "Email:" in body:
            email = body.split("Email:")[1].split("\n")[0].strip()

        if "Topilgan kurslar:" in body:
            courses = body.split("Topilgan kurslar:")[1].split("\n")[0].strip()

        browser.close()

        return {
            "pinfl": data.pinfl,
            "email": email,
            "courses": courses
        }
