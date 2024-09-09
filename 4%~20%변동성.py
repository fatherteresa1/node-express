import requests
import json
import datetime
import time
import yaml
import tkinter as tk
from tkinter import scrolledtext
import threading

with open('config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
ACCESS_TOKEN = ""
CANO = _cfg['CANO']
ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
DISCORD_WEBHOOK_URL = _cfg['DISCORD_WEBHOOK_URL']
URL_BASE = _cfg['URL_BASE']

# GUI 창에 출력하기 위한 함수 추가
def log_message(msg):
    now = datetime.datetime.now()
    log_textbox.insert(tk.END, f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    log_textbox.see(tk.END)
    log_textbox.update()

# 디스코드로 메세지를 보내는 함수는 그대로 사용
def send_message(msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)
    log_message(msg)

# 토큰 발급
def get_access_token():
    headers = {"content-type": "application/json"}
    body = {"grant_type": "client_credentials",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET}
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    ACCESS_TOKEN = res.json()["access_token"]
    return ACCESS_TOKEN

# 해시키 생성
def hashkey(datas):
    PATH = "uapi/hashkey"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        'content-Type': 'application/json',
        'appKey': APP_KEY,
        'appSecret': APP_SECRET,
    }
    res = requests.post(URL, headers=headers, data=json.dumps(datas))
    hashkey = res.json()["HASH"]
    return hashkey

# 전일 종가 조회
def get_previous_close_price(code="005930"):
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "FHKST01010400"}
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": code,
        "fid_org_adj_prc": "1",
        "fid_period_div_code": "D"
    }
    res = requests.get(URL, headers=headers, params=params)
    prev_close_price = int(res.json()['output'][1]['stck_clpr'])  # 전일 종가
    return prev_close_price

# 현재가 조회
def get_current_price(code="005930"):
    PATH = "uapi/domestic-stock/v1/quotations/inquire-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "FHKST01010100"}
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": code,
    }
    res = requests.get(URL, headers=headers, params=params)
    return int(res.json()['output']['stck_prpr'])

# 목표가 조회
def get_target_price(code="005930"):
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "FHKST01010400"}
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": code,
        "fid_org_adj_prc": "1",
        "fid_period_div_code": "D"
    }
    res = requests.get(URL, headers=headers, params=params)
    stck_oprc = int(res.json()['output'][0]['stck_oprc'])  # 오늘 시가
    stck_hgpr = int(res.json()['output'][1]['stck_hgpr'])  # 전일 고가
    stck_lwpr = int(res.json()['output'][1]['stck_lwpr'])  # 전일 저가
    target_price = stck_oprc + (stck_hgpr - stck_lwpr) * 0.6
    return target_price

# 주식 잔고 조회
def get_stock_balance():
    PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "TTTC8434R",
               "custtype": "P",
               }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    send_message(f"====주식 보유잔고====")
    for stock in stock_list:
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = stock['hldg_qty']
            send_message(f"{stock['prdt_name']}({stock['pdno']}): {stock['hldg_qty']}주")
            time.sleep(0.1)
    send_message(f"주식 평가 금액: {evaluation[0]['scts_evlu_amt']}원")
    time.sleep(0.1)
    send_message(f"평가 손익 합계: {evaluation[0]['evlu_pfls_smtl_amt']}원")
    time.sleep(0.1)
    send_message(f"총 평가 금액: {evaluation[0]['tot_evlu_amt']}원")
    time.sleep(0.1)
    send_message(f"=================")
    return stock_dict

# 현금 잔고 조회
def get_balance():
    PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-order"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "TTTC8908R",
               "custtype": "P",
               }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": "005930",
        "ORD_UNPR": "65500",
        "ORD_DVSN": "01",
        "CMA_EVLU_AMT_ICLD_YN": "Y",
        "OVRS_ICLD_YN": "Y"
    }
    res = requests.get(URL, headers=headers, params=params)
    cash = res.json()['output']['ord_psbl_cash']
    send_message(f"주문 가능 현금 잔고: {cash}원")
    return int(cash)

# 주식 매수
def buy(code="005930", qty="1"):
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01",
        "ORD_QTY": str(int(qty)),
        "ORD_UNPR": "0",
    }
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "TTTC0802U",
               "custtype": "P",
               "hashkey": hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        send_message(f"[매수 성공]{str(res.json())}")
        return True
    else:
        send_message(f"[매수 실패]{str(res.json())}")
        return False

# 주식 매도
def sell(code="005930", qty="1"):
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01",
        "ORD_QTY": qty,
        "ORD_UNPR": "0",
    }
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "TTTC0801U",
               "custtype": "P",
               "hashkey": hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        send_message(f"[매도 성공]{str(res.json())}")
        return True
    else:
        send_message(f"[매도 실패]{str(res.json())}")
        return False

# 매수 조건에서 전일 종가 대비 4% 이상, 20% 이하로 상승한 종목을 매수하도록 수정
def start_trading():
    try:
        global ACCESS_TOKEN
        ACCESS_TOKEN = get_access_token()

        symbol_list = ["098120", "058820", "050120", "024850", "024120", "079940", "078890", "036620", "114190", "094480", "011040", "024910", "049720", "014570", "035290", "121440", "029480", "026910", "053270", "066620", "043650", "006050", "060480", "035080", "114450", "083450", "204620", "053260", "282720", "036190","308100", "121600", "039860", "091970", "405920", "051490", "190510", "089600", "293580", "130580", "036800", "091590", "212560", "095660", "042420", "085910", "092730", "007390", "033640", "330860","160550", "225570", "217270", "104620", "194700", "285490", "145170", "142280", "234690", "054050", "040160", "270870", "085670", "064260", "039560", "154040", "032190", "068240", "020400", "008830","048470", "004780", "017650", "007720", "290670", "078140", "036480", "027830", "020180", "108380", "048910", "005710", "120240", "003310", "078600", "140520", "010170", "054670", "023910", "021040","021045", "067080", "298540", "089230", "224060", "317330", "263600", "263800", "067990", "006620", "005160", "075970", "100130", "099410", "033500", "025950", "088130", "041930", "060380", "079960","228340", "088910", "013120", "109860", "032960", "005290", "073190", "030350", "060570", "016670", "187870", "263690", "263720", "241520", "290120", "025440", "066900", "180400", "092070", "068790","039840", "104460", "079810", "113810", "068930", "033130", "060900", "105740", "290550", "066670", "383930", "171120", "084650", "038390", "294140", "228670", "228850", "090360", "067730", "071280","038060", "016100", "012700", "073570", "277070", "042500", "195500", "169330", "038290", "267980", "005990", "093520", "100590", "067280", "072870", "133750", "446540", "041920", "014100", "086900", "021880", "140410", "059210", "080420", "417970", "080160", "101330", "012860", "118990", "001810", "095500", "100790", "049950", "059090", "201490", "206640", "018700", "035620", "053030", "064550","038460", "099430", "032980", "043150", "267790", "046310", "206400", "019010", "225530", "250000", "006910", "008470", "014470", "100120", "406820", "337930", "251630", "018290", "033560", "126340","082800", "318410", "141000", "083650", "065170", "086670", "126600", "082920", "042370", "050090", "093190", "210120", "044480", "072950", "451250", "143240", "419120", "014970", "018310", "053700","023600", "009300", "060310", "054540", "032280", "002290", "037460", "032750", "054090", "000250", "024950", "038500", "017480", "027580", "038540", "091580", "263810", "089980", "042940", "042600","038070", "006730", "100660", "019770", "043710", "092190", "063170", "027040", "093920", "178320", "122690", "011370", "065710", "035890", "003100", "171090", "086710", "014620", "037350", "081580","045300", "015750", "080470", "043260", "148150", "053060", "017510", "011560", "024830", "036630", "039310", "067770", "053450", "108860", "068760", "060230", "290690", "066910", "035610", "357780","086980", "084180", "253840", "236200", "192440", "099440", "060240", "115570", "330730", "415380", "013810", "049830", "020710", "033170", "048870", "025320", "025870", "215600", "065350", "416180","002800", "017000", "012790", "138070", "056700", "243840", "036710", "160980", "037760", "099320", "049960", "050890", "013720", "109670", "264660", "352700", "056730", "297090", "115480", "376290", "051500", "096530", "060590", "260930", "052300", "013990", "125210", "052710", "083930", "149950", "036010", "050860", "127710", "227610", "143160", "054800", "332370", "099190", "461300", "289010","214430", "040910", "095340", "069920", "052220", "090150", "031310", "052460", "119830", "052770", "027360", "032080", "013310", "001540", "053800", "260660", "361570", "218410", "061040", "085810","314140", "205500", "052790", "030960", "102120", "019990", "038680", "121890", "099220", "289080", "019550", "042110", "036120", "101490", "095910", "031330", "060540", "036540", "080000", "091340","063440", "041510", "048550", "007820", "109610", "365330", "306040", "016250", "040610", "069510", "234300", "039440", "098660", "050760", "058610", "043340", "200710", "195990", "003800", "241840","312610", "297890", "440290", "078150", "072990", "036640", "028300", "067630", "115450", "239610", "148930", "357230", "071670", "045660", "224110", "021080", "262260", "265520", "054620", "109960","230240", "038870", "097780", "448280", "038110", "214270", "036810", "173940", "054940", "092870", "067570", "101400", "078860", "104200", "053290", "198080", "048830", "376190", "061970", "309960","290650", "060370", "417200", "078020", "083310", "037950", "058630", "179290", "009780", "123040", "033160", "033310", "259630", "105550", "036560", "265560", "036000", "053280", "045060", "039830","046120", "014940", "065500", "010470", "053980", "052420", "031510", "080580", "067170", "353590", "173130", "049480", "057540", "131030", "082210", "057030", "122990", "065530", "067900", "007530","155650", "019210", "040300", "079000", "032820", "041190", "046970", "082850", "072470", "073560", "037400", "153490", "101170", "066590", "046940", "065680", "018620", "457550", "032940", "104830","014190", "217820", "030530", "012620", "008370", "008290", "101160", "065950", "076080", "043590", "053580", "044340", "348350", "112040", "101730", "123420", "299900", "036090", "136540", "097800","036200", "018000", "011320", "086390", "241690", "142210", "048430", "089850", "032620", "264450", "078070", "024800", "054930", "049520", "023410", "056080", "084370", "240600", "191410", "072770","039020", "067920", "044960", "302430", "056090", "073490", "088390", "053350", "054210", "009730", "080010", "102710", "041520", "123570", "083470", "095190", "091120", "088290", "037370", "035810","092130", "001840", "041830", "079950", "060150", "033230", "037330", "100030", "064090", "216050", "049070", "017250", "051370", "064290", "189300", "039290", "071200", "101930", "019540", "094820","049550", "049630", "040420", "045510", "217190", "122310", "361390", "159580", "033100", "079370", "067290", "054950", "023440", "090470", "137950", "033320", "204270", "026040", "126880", "033050","094970", "199820", "038010", "080220", "034940", "067000", "033340", "000440", "051980", "043610", "036180", "144510", "051160", "053050", "130500", "119850", "065060", "388050", "018120", "086060","036890", "007370", "085660", "094850", "004650", "278280", "362320", "066360", "016920", "071850", "050110", "063080", "307930", "263700", "221980", "024840", "021320", "036670", "115500", "089150", "025880", "093320", "101000", "073010", "060720", "122450", "052900", "105330", "053080", "058400", "272110", "039420", "083550", "032500", "046440", "151860", "035600", "036030", "064820", "024880","258610", "089010", "052400", "047770", "027050", "190650", "049430", "089890", "222040", "241710", "045970", "196450", "029960", "102940", "033290", "056360", "282880", "015710", "052330", "060280","182360", "066310", "016600", "096240", "040350", "110790", "045520", "036170", "237880", "139670", "054780", "219130", "065130", "134580", "023160", "044490", "066700", "095610", "064520", "089030","054450", "215480", "026150", "033830", "340570", "043220", "131290", "246690", "131100", "356860", "241790", "032540", "022220", "104480", "081150", "130740", "084730", "033540", "177830", "037070","037030", "047310", "170790", "038950", "441270", "106240", "131760", "140860", "318010", "027710", "068050", "251970", "119500", "472850", "039980", "041910", "041020", "114630", "290720", "005670","007330", "093380", "023900", "445180", "053610", "053160", "237820", "023770", "019570", "033790", "032580", "051380", "031980", "002230", "043370", "347740", "128660", "006140", "062970", "378340","161580", "347770", "067310", "136480", "013030", "126700", "106080", "160190", "221840", "106190", "065650", "066130", "039340", "034950", "025550", "017890", "063570", "041460", "101680", "039740","053300", "025770", "023760", "054040", "021650", "032300", "037230", "030520", "052600", "092460", "047080", "452280", "066980", "114810", "070590", "078350", "045100", "024740", "005860", "007770","198940", "058450", "079170", "054920", "034810", "03481K", "076610", "214180", "234340", "170030", "052260", "048410", "041440", "039010", "090850", "460930", "092300", "138360", "011080", "060560","064240", "039610", "061250", "097870", "192410", "090710", "078590", "115160", "028080", "200670", "065510", "084110", "010240", "037440"]  # 예시 종목 리스트
        bought_list = []  # 매수 완료된 종목 리스트
        total_cash = get_balance()  # 보유 현금 조회
        stock_dict = get_stock_balance()  # 보유 주식 조회
        for sym in stock_dict.keys():
            bought_list.append(sym)
        target_buy_count = 6  # 매수할 종목 수
        buy_percent = 0.16  # 종목당 매수 금액 비율
        buy_amount = total_cash * buy_percent  # 종목별 주문 금액 계산
        soldout = False

        send_message("===국내 주식 자동매매 프로그램을 시작합니다===")
        while True:
            t_now = datetime.datetime.now()
            t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
            t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
            t_sell = t_now.replace(hour=15, minute=15, second=0, microsecond=0)
            t_exit = t_now.replace(hour=15, minute=20, second=0, microsecond=0)
            today = datetime.datetime.today().weekday()
            if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
                send_message("주말이므로 프로그램을 종료합니다.")
                break
            if t_9 < t_now < t_start and soldout == False:  # 잔여 수량 매도
                for sym, qty in stock_dict.items():
                    sell(sym, qty)
                soldout = True
                bought_list = []
                stock_dict = get_stock_balance()
            if t_start < t_now < t_sell:  # AM 09:05 ~ PM 03:15 : 매수
                for sym in symbol_list:
                    if len(bought_list) < target_buy_count:
                        if sym in bought_list:
                            continue
                        target_price = get_target_price(sym)
                        current_price = get_current_price(sym)
                        previous_close = get_previous_close_price(sym)
                        # 전일 종가 대비 4% 이상 20% 이하 상승했는지 체크
                        if 1.04 <= current_price / previous_close <= 1.20 and current_price > 1500:
                            buy_qty = 0  # 매수할 수량 초기화
                            buy_qty = int(buy_amount // current_price)
                            if buy_qty > 0:
                                send_message(f"{sym} 4% ~ 20% 상승 조건 달성 및 목표가 달성({target_price} < {current_price}) 매수를 시도합니다.")
                                result = buy(sym, buy_qty)
                                if result:
                                    soldout = False
                                    bought_list.append(sym)
                                    get_stock_balance()
                        time.sleep(1)
                time.sleep(1)
                if t_now.minute == 30 and t_now.second <= 5:
                    get_stock_balance()
                    time.sleep(5)
            if t_sell < t_now < t_exit:  # PM 03:15 ~ PM 03:20 : 일괄 매도
                if soldout == False:
                    stock_dict = get_stock_balance()
                    for sym, qty in stock_dict.items():
                        sell(sym, qty)
                    soldout = True
                    bought_list = []
                    time.sleep(1)
            if t_exit < t_now:  # PM 03:20 ~ :프로그램 종료
                send_message("프로그램을 종료합니다.")
                break
    except Exception as e:
        send_message(f"[오류 발생] {e}")
        time.sleep(1)

# GUI 창 생성 및 실행
def run_gui():
    global log_textbox
    root = tk.Tk()
    root.title("자동매매 프로그램")
    
    # 로그 표시창 생성
    log_textbox = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=30, font=("Helvetica", 10))
    log_textbox.pack(padx=10, pady=10)

    # 프로그램 시작 버튼
    start_button = tk.Button(root, text="자동매매 시작", command=lambda: threading.Thread(target=start_trading).start(), height=2, width=20)
    start_button.pack(pady=10)

    # 프로그램 종료 버튼
    exit_button = tk.Button(root, text="프로그램 종료", command=root.quit, height=2, width=20)
    exit_button.pack(pady=10)

    root.mainloop()

# GUI 실행
run_gui()
