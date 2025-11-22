# PayPay.PY
Python用のPayPay APIライブラリです。

## インストール
```bash
コマンド
```

## 機能
- `login_start` or `login_confirm` - ログイン
- `get_profile` - プロフィール情報を取得
- `get_balance` - 残高を取得
- `get_claim` - 請求リンクを取得
- `check_link` - P2Pリンクの情報を取得
- `accept_link` - P2Pリンクを受け取る
- `reject_link` - P2Pリンクを辞退する
- `create_link` - P2Pリンクを作成する
- `bypass` - Bot検知を回避する(AWS-WAFとは別)

## AWS-WAF
2025年11月07日、PayPayはログイン時に「Aws Waf」というBot検知システムを追加しました。<br>
このライブラリは「Aws Waf」のSolve機能を搭載しており、通常通りログインできます。