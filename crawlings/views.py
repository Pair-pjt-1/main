from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from .models import Crawlings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime

Comment = get_user_model()

# Create your views here.
def index(request):
    company_info = request.GET.get('title')
    context = {
        'company_info': company_info,
    }
    return render(request, 'crawlings/index.html', context)

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


def find(request):
    if request.method == 'POST':
        stock_name = request.POST.get('title')

        # 크롤링 실행
        stock_name, code, comments = crawl_toss_comments_by_name(stock_name)

        # DB 저장
        for c in comments:
            Crawlings.objects.create(
                title = stock_name,
                code= code,
                comment=c['comment'],
            )
        
        # 3. 저장한 결과 다시 읽기
        results = Crawlings.objects.filter(title=stock_name).order_by('-updated_at')

        return render(request, 'crawlings/index.html', {
            'company_info': {
                'title': stock_name,
                'code': code,
                'comments': results,
            }
        })
    else:
        return render(request, 'crawlings/index.html')

def delete_comment(request, pk):
    if request.method == 'POST':
        title = request.POST.get('title')
        comment = Crawlings.objects.get(pk=pk)
        comment.delete()

        results = Crawlings.objects.filter(title=title)
        code = results.first().code if results.exists() else '000000'
        return render(request, 'crawlings/index.html', {
            'company_info': {
                'title': title,
                'code': code,
                'comments': results,
            }
        })
    else:
        return redirect('crawlings:index')
