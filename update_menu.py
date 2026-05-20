from playwright.sync_api import sync_playwright
import csv
import time

def scrape_komaba_menu():
    # 実際の対象URL
    target_url = "https://comenu.jp/tokyo-univ/390154/menu"
    extracted_data = []

    # 取得したいカテゴリ名のリスト
    categories = ["主菜", "副菜・サラダ", "丼物・カレー", "麺類", "ごはん", "汁物", "デザート"]

    with sync_playwright() as p:
        # headless=False のままであれば、実際のブラウザが動く様子を観察できる
        
        # 変更前
        # browser = p.chromium.launch(headless=False)

        # 変更後（画面を出さずに裏で実行するモード）
        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        # --- 1. カテゴリごとの大きなループ ---
        for category in categories:
            print(f"\n=== 【{category}】のデータ取得を開始 ===")
            
            # カテゴリが変わるたびに一度メニュー一覧のトップページを開き直す
            page.goto(target_url)
            page.wait_for_load_state("networkidle")
            time.sleep(1)

            try:
                # 対象のカテゴリをクリックして展開
                # 【変更前】部分一致だったため「黒米麦ごはん」などに反応してエラーになっていた
                # page.locator(f"text={category}").click()
                
                # 【変更後】h3タグかつ完全一致で探すことで、確実にカテゴリの見出しだけを撃ち抜く
                page.locator(f"h3:text-is('{category}')").click()
                time.sleep(1)

                # 【修正】特定のカテゴリ名を持つアコーディオン(details)の中だけに絞り込む
                category_container = page.locator(f"details:has(h3:text-is('{category}'))")
                
                # その中にある商品要素だけを取得する
                item_locator = category_container.locator("a.col-span-1.bg-white.shadow-md")
                item_count = item_locator.count()
                print(f"「{category}」の商品を {item_count} 件検出。")

                # --- 2. 各カテゴリ内の商品ごとの小さなループ ---
                for i in range(item_count):
                    try:
                        print(f"{category} {i+1}/{item_count} 件目を処理中...")

                        # メニュー一覧ページにいない場合「のみ」一覧へ戻る
                        if page.url != target_url:
                            page.goto(target_url)
                            page.wait_for_load_state("networkidle")
                            time.sleep(1)

                        # 【修正】絞り込んだカテゴリの中からi番目の商品を指定
                        item = item_locator.nth(i)
                        
                        # 商品のHTMLから、リンク先（href）の文字列を直接抜き出す
                        href = item.get_attribute("href")
                        
                        # 抜き出したリンクと、サイトのドメインを合体させて完全なURLを作る
                        detail_url = "https://comenu.jp" + href
                        
                        # アニメーションや重なりを無視して、そのURLへ直接ジャンプ！
                        page.goto(detail_url)
                        page.wait_for_load_state("networkidle")
                        time.sleep(1)

                       

                        # --- 詳細画面でのデータ抽出 ---
                        item_name = page.locator("h2").first.inner_text().strip()
                        price = page.locator("span.text-2xl").inner_text().strip()
                        
                        # 栄養素の取得
                        energy = page.locator("dt:text-is('エネルギー') + dd").inner_text().strip()
                        protein = page.locator("dt:text-is('蛋白質') + dd").inner_text().strip()
                        fat = page.locator("dt:text-is('脂質') + dd").inner_text().strip()
                        carbs = page.locator("dt:text-is('炭水化物') + dd").inner_text().strip()
                        salt = page.locator("dt:text-is('食塩相当量') + dd").inner_text().strip()
                        calcium = page.locator("dt:text-is('カルシウム') + dd").inner_text().strip()
                        vegetable = page.locator("dt:text-is('野菜量') + dd").inner_text().strip()
                        iron = page.locator("dt:text-is('鉄') + dd").inner_text().strip()
                        vit_a = page.locator("dt:text-is('ビタミンA') + dd").inner_text().strip()
                        vit_b1 = page.locator("dt:text-is('ビタミンB1') + dd").inner_text().strip()
                        vit_b2 = page.locator("dt:text-is('ビタミンB2') + dd").inner_text().strip()
                        vit_c = page.locator("dt:text-is('ビタミンC') + dd").inner_text().strip()

                        # --- アレルギー情報の取得 ---
                        try:
                            # 「アレルギー情報」の次にある <ul> の中の <img> タグをすべて探す
                            allergy_images = page.locator("h3:text-is('アレルギー情報') + ul img")
                            
                            # JavaScriptの機能を使って、全画像の 'alt' 属性の文字をリストとして一気に抜き出す
                            allergy_list = allergy_images.evaluate_all("imgs => imgs.map(img => img.alt)")
                            
                            if allergy_list:
                                # ['小麦', '鶏肉', '大豆'] を 「小麦、鶏肉、大豆」 のようにつなげる
                                allergy = "、".join(allergy_list)
                            else:
                                allergy = "なし"
                        except Exception as e:
                            allergy = "なし"       


                        # データリストに追加
                        extracted_data.append({
                            "カテゴリ": category,
                            "商品名": item_name,
                            "価格": price,
                            "エネルギー": energy,
                            "蛋白質": protein,
                            "脂質": fat,
                            "炭水化物": carbs,
                            "食塩相当量": salt,
                            "カルシウム": calcium,
                            "野菜量": vegetable,
                            "鉄": iron,
                            "ビタミンA": vit_a,
                            "ビタミンB1": vit_b1,
                            "ビタミンB2": vit_b2,
                            "ビタミンC": vit_c,
                            "アレルギー": allergy
                        })

                    except Exception as e:
                        print(f"エラー発生 ({category}の{i+1}件目): {e}")

            except Exception as e:
                print(f"カテゴリ「{category}」の展開中にエラー発生: {e}")

        browser.close()

   
    # --- 3. 抽出したデータをCSVファイルに出力 ---
    
    # GitHub Actionsでの自動化に合わせて、相対パス（ファイル名のみ）に変更
    csv_filename = "menu_data.csv"

    with open(csv_filename, mode="w", encoding="utf-8-sig", newline="") as f:
        # カテゴリ列を追加したヘッダー
        headers = ["カテゴリ", "商品名", "価格", "エネルギー", "蛋白質", "脂質", "炭水化物", "食塩相当量", "カルシウム", "野菜量", "鉄", "ビタミンA", "ビタミンB1", "ビタミンB2", "ビタミンC", "アレルギー"]
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(extracted_data)

    print(f"全カテゴリのスクレイピング完了。データは {csv_filename} に保存された。")
    

if __name__ == "__main__":
    scrape_komaba_menu()


#実行　ターミナルで以下を入力して実行してください。
# python3 /Users/kurebayashisosuke/Desktop/menu_scraper/menu_playwright.py
