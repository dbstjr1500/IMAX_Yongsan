# IMAX_Yongsan

## 현재까지 구현된 기능
>1. 5초마다 cgv 홈페이지를 확인하여 용아맥 예매가 열렸는지 확인여부
>2. 매일 낮 11시 59분에 봇이 정상작동중인지 메시지 출력

## 차후 구현예정인 기능
>1. 텔레그램 봇 명령어를 이용하여 봇 정상작동 여부 상시 체크
>2. 현재 수동으로 입력해야하는 날짜 정보 자동 입력
>    * 내일 날짜로부터 시작해 약 15일간의 날짜정보를 모두 리스트에 저장
>    * 이후 해당 행위를 지속적으로 반복하며 리스트에 저장된 데이터와 비교 후 새로운 데이터일 시 텔레그램 메세지 출력
>    * 새롭게 추가된 데이터를 확인하여 연속된 작은 숫자가 2개이상 리스트에 있을경우 해당 지점으로부터 15일치 스캔

## 수정 예정인 부분
>1. 봇 정상작동 출력 메세지가 총 12회 출력되는 문제

## 차후 구현하고자 하는 기능
>1. 텔레그램 봇 명령어를 이용하여 현재 열린 예매날짜, 시간대, 남은 자릿수 확인
>2. 텔레그램 봇 명령어를 이용하여 특정 자리 지정 후, 해당 자리 및 주변 자리 예매 취소시 알림
