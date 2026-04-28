def Get_Assessment_From_OpenAi_Api(url):
    try:
        from openai import OpenAI
        # client = OpenAI()
        client = OpenAI(api_key="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")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict E-commerce Checkout UX and SEO evaluator. "
                        "You MUST evaluate websites using 23 predefined usability rules. "
                        "You ALWAYS return structured JSON output."
                    )
                },
                {
                    "role": "user",
                    "content": f"""
Analyze this website checkout URL: {url}

Evaluate it strictly based on these 23 usability rules:

Category 1: Navigation & Step Clarity
R1: Steps clearly marked
R2: Clear button labels
R3: CTA always visible

Category 2: Transparency & Trust
R4: Explain personal info
R5: Show all costs early
R6: Security indicators visible
R7: Return policy accessible
R8: Delivery time shown

Category 3: Form Design
R9: Minimal steps
R10: Progress indicator + simplified forms
R11: Minimal form fields
R12: Clear error messages

Category 4: User Control
R13: Guest checkout available
R14: Editable cart
R15: Order summary before payment
R16: Mobile optimized

Category 5: Payment & Product
R17: Multiple payment options
R18: Buy Now option
R19: Reviews visible

Category 6: UI & Design
R20: CTA prominent
R21: No clutter
R22: Consistent branding
R23: Clear product info

---

Return ONLY valid JSON in this format:

{{
  "seo_score": X,
  "ux_score": X,
  "total_rules": 23,
  "passed_rules": ["R1", "R2"],
  "failed_rules": ["R5", "R10"],
  "score": X,
  "performance": "Critical/Poor/Average/Good/Excellent",
  "summary": "short explanation"
}}

Scoring logic:
- Score = number of passed rules
- Performance:
  0-5 = Critical
  6-10 = Poor
  11-15 = Average
  16-20 = Good
  21-23 = Excellent
"""
                }
            ]
        )

        result = response.choices[0].message.content

        print(result)
        return result

    except Exception as e:
        print("OpenAI Error:", e)
        return None


#test the script with openai api
url = "https://uk.gymshark.com"
Get_Assessment_From_OpenAi_Api(url)