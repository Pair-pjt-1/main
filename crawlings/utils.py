import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import sys
import django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finance_pjt.settings")
django.setup()
from openai import OpenAI
from dotenv import load_dotenv
from openai import OpenAI

def crawl_toss_comments_by_name(search_keyword, target_count=20):
    stock_name = search_keyword  # ✅ 기본값 세팅
    code = "000000"
    comments = []

    options = Options()
    options.add_argument("--headless")  # 배포 환경에서는 활성화 가능
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    try:
        # 1. 토스 메인 페이지 접속
        driver.get("https://tossinvest.com/")
        time.sleep(2)

        # 2. 돋보기 아이콘(검색 버튼) 클릭 → 검색창 열기
        search_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[aria-haspopup="dialog"]')
        ))
        search_button.click()
        time.sleep(1)

        # 3. 팝업으로 열린 검색창 input 태그에 종목명 입력
        search_input = wait.until(EC.element_to_be_clickable(
            (By.CLASS_NAME, "_1x1gpvi6")
        ))
        search_input.send_keys(stock_name)
        time.sleep(1)
        search_input.send_keys(Keys.RETURN)

        # 4. 종목 상세 페이지 로딩 대기
        wait.until(EC.url_contains("/stocks/"))
        time.sleep(2)

        # 9. 종목 코드 추출
        try:
            # _1sivumi0 클래스 안의 첫 번째 div 내 span 두 개 가져오기
            info_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, '_1sivumi0')))
            first_row_div = info_div.find_element(By.TAG_NAME, 'div')  # 첫 번째 div (종목명 + 코드)
            spans = first_row_div.find_elements(By.CLASS_NAME, 'tw-1r5dc8g0')

            stock_name = spans[0].text.strip()
            code = spans[1].text.strip()
        except Exception as e:
            print(f"[에러] 종목명/코드 추출 실패: {e}")
            # stock_name = search_keyword
            # code = "000000"

        # 5. 커뮤니티 탭 클릭
        community_tab = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[data-contents-label="커뮤니티"]')
        ))
        community_tab.click()

        # 6. 커뮤니티 페이지 로딩 대기
        wait.until(EC.url_contains("/community"))
        time.sleep(2)

        # 7. 댓글 더 많이 로드되도록 스크롤 반복
        for _ in range(10):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
            spans = driver.find_elements(By.CLASS_NAME, "_60z0ev1")
            if len(spans) >= target_count:
                break

        # 8. 댓글 내용 추출
        comments = []
        for span in spans[:target_count]:
            text = span.text.strip()
            if len(text) < 80:
                comments.append({
                    "stock_name": stock_name,
                    "comment": text,
                    "created_at": datetime.now()
                })

        return stock_name, code, comments

    finally:
        driver.quit()


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

def get_comment_form_OpenAI(comments):
    if not comments:
        return "해당 종목에 대한 댓글이 없어 분석할 수 없습니다."

    comment_text = "\n".join(comments)
    
    try:
        response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
            "role": "system",
            "content": [
                {
                "type": "input_text",
                "text": "너는 증권 웹사이트에서 댓글들의 내용을 분석하고 현재 해당 주식에 대한 주주들의 여론을 판단하는 금융 AI야."
                "내가 주는 댓글들을 읽어보고 주주들의 두드러지는 의견을 3가지 정도 제시해주고 현재 여론이 긍정적인지 부정적인지 혹은 중립적인지 마지막에 결론지어줘."
                "너의 답변은 보고서 형식으로 3가지 특징을 간단히 요약해서 알려주고 그로 인해 여론은 어떠한 상태로 유추할 수 있다고 결론내리는 형식으로 답변해줘"
                "보고서 형식을 유지하되 소제목은 사용하지 말고 하나의 문단으로 답변을 완성해줘"
                }
            ]
            },
            {
            "role": "user",
            "content": [
                {
                "type": "input_text",
                "text": comment_text
                }
            ]
            }
        ],
        temperature=1,
        max_output_tokens=512
        )

        return response.output_text
    
    except Exception as e:
        return f'GPT 분석 중 오류가 발생했습니다.: {e}'