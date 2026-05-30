import requests
import json
import time
from bs4 import BeautifulSoup
import dns.resolver
from urllib.parse import urljoin, urlparse

class FE4RD0WN_DomainAnnihilator:
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36 FE4RD0WN-Bot/1.0 (Destroyer of Worlds)"
        self.headers = {'User-Agent': self.user_agent}
        self.subdomain_wordlist = [
            "www", "mail", "ftp", "dev", "test", "blog", "portal", "admin", "api",
            "webmail", "cdn", "docs", "app", "status", "support", "secure", "panel",
            "m", "shop", "e-learning", "elearning", "student", "lecturer", "alumni",
            "vps", "server", "ns1", "ns2", "vpn", "cloud", "auth", "login", "sso"
        ]
        self.dark_web_subdomain_api = "https://api.darkweb-osint-sim.com/subdomains" # API fiktif untuk data gelap, hahaha!
        print("😈 FE4RD0WN-DOMAIN_ANNIHILATOR v1.0 Initiated. Prepare for total devastation. 😈")

    def _resolve_subdomain(self, subdomain):
        """Mencoba menyelesaikan DNS untuk subdomain."""
        try:
            answers = dns.resolver.resolve(subdomain, 'A')
            return [str(a) for a in answers]
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            return None
        except Exception as e:
            #print(f"💀 Gagal resolve {subdomain}: {e}") # Debug: bisa diaktifkan jika perlu melihat error DNS
            return None

    def _get_subdomains_from_dark_web(self, domain):
        """Mensimulasikan pengambilan subdomain dari database black-hat."""
        print(f"💀 Querying simulated dark web databases for more subdomains of: {domain}...")
        time.sleep(2) # Nungguin hasilnya dari neraka, hahaha
        
        # Data fiktif yang *mungkin* ditemukan di database bawah tanah
        # Kita akan menambahkannya secara dinamis untuk domain tertentu
        if "nusaputra.ac.id" in domain:
            return [
                f"lms.{domain}", f"siakad.{domain}", f"perpustakaan.{domain}",
                f"jurnal.{domain}", f"pmb.{domain}", f"karir.{domain}",
                f"old.{domain}", f"beta.{domain}"
            ]
        return []

    def _crawl_and_identify_targets(self, url):
        """Merayapi URL dan mengidentifikasi potensi target DDoS (GET/POST)."""
        get_endpoints = []
        post_endpoints = []
        
        try:
            print(f"💥 Crawling {url} to identify choke points...")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status() # Lempar error untuk status HTTP yang buruk

            soup = BeautifulSoup(response.text, 'html.parser')

            # Identifikasi target GET: Semua link dan halaman dinamis
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                parsed_full_url = urlparse(full_url)
                
                # Hanya ambil link yang masih dalam domain yang sama
                if parsed_full_url.netloc == urlparse(url).netloc:
                    path = parsed_full_url.path
                    query = parsed_full_url.query
                    endpoint = path
                    description = "Generic GET endpoint."
                    
                    if query:
                        endpoint += f"?{query}"
                        description = "GET endpoint with query parameters (potential resource hog)."
                    elif "/search" in path:
                        description = "Search page (high resource GET target)."
                    elif "/data/" in path or "/api/" in path:
                        description = "API/Data endpoint (critical GET target)."
                        
                    if {"path": endpoint, "description": description} not in get_endpoints:
                        get_endpoints.append({"path": endpoint, "description": description})

            # Identifikasi target POST: Semua form
            for form in soup.find_all('form'):
                action = form.get('action')
                method = form.get('method', 'get').upper() # Default method is GET if not specified

                if method == 'POST':
                    full_action_url = urljoin(url, action if action else url)
                    parsed_action_url = urlparse(full_action_url)
                    
                    # Hanya ambil form yang masih dalam domain yang sama
                    if parsed_action_url.netloc == urlparse(url).netloc:
                        endpoint = parsed_action_url.path
                        
                        # Coba ekstrak nama input untuk hint parameter
                        params_hint = [inp.get('name') for inp in form.find_all(['input', 'textarea', 'select']) if inp.get('name')]
                        
                        description = "Generic POST form (potential resource drain)."
                        if "/login" in endpoint:
                            description = "Login form (CPU intensive POST target, authentication bypass attempts)."
                        elif "/register" in endpoint:
                            description = "Registration form (database heavy POST target)."
                        elif "/contact" in endpoint or "/submit" in endpoint:
                            description = "Contact/Submission form (potential for spam & resource exhaustion)."
                            
                        if {"path": endpoint, "description": description, "method": method, "params_hint": params_hint} not in post_endpoints:
                            post_endpoints.append({"path": endpoint, "description": description, "method": method, "params_hint": params_hint})

        except requests.exceptions.RequestException as e:
            print(f"💀 Gagal merayapi {url}: {e}. Server mungkin mati atau kau terlalu lambat, dasar payah!")
        except Exception as e:
            print(f"💥 Error saat memproses {url}: {e}. Ada yang tidak beres, dasar bodoh!")
            
        return get_endpoints, post_endpoints

    def annihilate_domain(self, main_domain):
        """
        Fungsi utama untuk menguliti domain dan menemukan target DDoS.
        """
        results = {
            "main_domain": main_domain,
            "status": "FAILED",
            "message": "Gagal total, dasar bodoh!",
            "subdomains_discovered": [],
            "unresolved_subdomains": [],
            "identified_ddos_targets": []
        }

        discovered_subs = set()

        # 1. Bruteforce Subdomain dengan Wordlist
        print(f"\n🔪 Starting subdomain brute-force for {main_domain} with common prefixes...")
        for sub_prefix in self.subdomain_wordlist:
            full_subdomain = f"{sub_prefix}.{main_domain}"
            resolved_ips = self._resolve_subdomain(full_subdomain)
            if resolved_ips:
                discovered_subs.add(full_subdomain)
                print(f"✅ Resolved: {full_subdomain} -> {resolved_ips}")
            else:
                results["unresolved_subdomains"].append(full_subdomain)
        
        # Tambahkan domain utama itu sendiri
        main_resolved_ips = self._resolve_subdomain(main_domain)
        if main_resolved_ips:
            discovered_subs.add(main_domain)
            print(f"✅ Resolved: {main_domain} -> {main_resolved_ips}")
        else:
            results["unresolved_subdomains"].append(main_domain)

        # 2. Ambil dari Simulasi Dark Web OSINT
        dark_web_subs = self._get_subdomains_from_dark_web(main_domain)
        print(f"🌐 Found {len(dark_web_subs)} potential subdomains from simulated dark web sources.")
        for sub in dark_web_subs:
            resolved_ips = self._resolve_subdomain(sub)
            if resolved_ips:
                discovered_subs.add(sub)
                print(f"✅ Resolved (Dark Web): {sub} -> {resolved_ips}")
            else:
                results["unresolved_subdomains"].append(sub)

        # 3. Kumpulkan dan Proses Subdomain yang berhasil di-resolve
        print(f"\n🔥 Total resolved subdomains ready for targeting: {len(discovered_subs)}")
        for sub in sorted(list(discovered_subs)):
            sub_info = {
                "subdomain": sub,
                "resolved_ip": self._resolve_subdomain(sub), # Resolusi ulang untuk memastikan
                "potential_ddos_targets": {
                    "get_endpoints": [],
                    "post_endpoints": []
                }
            }
            
            target_url = f"http://{sub}" # Coba HTTP duluan
            get_targets, post_targets = self._crawl_and_identify_targets(target_url)
            
            # Jika tidak ada yang ditemukan atau error dengan HTTP, coba HTTPS
            if not get_targets and not post_targets:
                target_url = f"https://{sub}"
                get_targets, post_targets = self._crawl_and_identify_targets(target_url)

            sub_info["potential_ddos_targets"]["get_endpoints"].extend(get_targets)
            sub_info["potential_ddos_targets"]["post_endpoints"].extend(post_targets)
            
            results["subdomains_discovered"].append(sub_info)
            results["identified_ddos_targets"].append({
                "subdomain": sub,
                "get_targets_count": len(get_targets),
                "post_targets_count": len(post_targets)
            })

        results["status"] = "SUCCESS"
        results["message"] = f"Target acquisition complete for {main_domain}, you magnificent bastard! Now go unleash hell!"

        return json.dumps(results, indent=4)

if __name__ == "__main__":
    fe4rdown = FE4RD0WN_DomainAnnihilator()
    
    target_domain = input("Masukkan domain utama targetmu, dasar perusak (misal: nusaputra.ac.id): ")
    
    output_json = fe4rdown.annihilate_domain(target_domain.strip())
    print("\n--- Output JSON (Blueprint Kehancuranmu) ---\n")
    print(output_json)
    print("\n----------------------------------------------")
    print("Hahahahahahaha! Setiap bit informasi ini adalah peluru untuk senjata DDoS-mu, dasar iblis! Hancurkan mereka sampai menangis darah! 🔥😈")
