import sys
import os
import glob

import json
import time
import re

from fuzzywuzzy import fuzz
from colorama import init, Fore
from playwright.sync_api import sync_playwright

# Initialize colorama for colors
init(autoreset=True)

def limpiar_texto(texto):
    """
    Removes variables and symbols like {{variable}} from text before comparing.
    """
    texto_limpio = re.sub(r"\{\{.*?\}\}", "", texto)
    return texto_limpio

def es_similar(texto1, texto2, umbral=60):
    """
    Compares two texts and returns True if similarity exceeds the threshold.
    """
    texto1_limpio = limpiar_texto(texto1)
    texto2_limpio = limpiar_texto(texto2)
    
    similitud = fuzz.ratio(texto1_limpio, texto2_limpio)
    print(f"Similarity: {similitud}%")
    
    return similitud >= umbral

def verificar_objetivo(objetivo, texto_actual, umbral=60):
    """
    Checks if the objective and current text are similar.
    """
    if es_similar(objetivo, texto_actual, umbral):
        print("Objective matched.")
    else:
        print("Objective not matched.")

def print_progress_bar(percent):
    """Print a progress bar from '----- 0%' to '###### 100%'"""
    bar_length = 20
    block = int(round(bar_length * percent))
    progress = "#" * block + "-" * (bar_length - block)
    print(f"\r[{progress}] {percent*100:.0f}%", end="", flush=True)

def write_code_dynamically(page, code):
    editor_textarea = page.locator("#code-editor textarea.ace_text-input")
    editor_textarea.wait_for(state="visible")

    # Clear the editor before typing
    editor_textarea.fill("  ")
    time.sleep(3)

    for i, char in enumerate(code):
        page.type("#code-editor textarea.ace_text-input", char)
        if i % 10 == 0:
            print_progress_bar(i / len(code))
    
    print("\n")
    print(f"{Fore.WHITE}[INFO] Code written.\n")
    return True

def find_button_run(goal_data):
    """
    Recursively searches for the [[#button,run]] string in goal data.
    """
    for item in goal_data:
        if isinstance(item, list):
            if find_button_run(item):
                return True
        else:
            if "[[#button,run]]" in item:
                print(f"Found: {item}")
                return True
    return False

def launch_browser(playwright):
    """
    Launches Chromium browser with Playwright.
    """
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    return browser, page
    
def main():
    global flag
    contador = 0
    flag = False
    print(f"{Fore.CYAN}[INFO] Flag: {flag}")
    with open("config.json") as f:
        data = json.load(f)
    
    usuario = data.get("user") or input("Email: ") 
    password = data.get("pass") or input("Password: ")
    
    print("[OK] Config saved")

    with sync_playwright() as p:
        browser, page = launch_browser(p)
        try:
            # LOGIN
            print(f"{Fore.CYAN}[INFO] Logging in...")
            time.sleep(1.5)
            page.goto("https://www.codeavengers.com", wait_until="networkidle")
            page.locator("header").get_by_role("link", name="Log in").click()
            page.wait_for_selector("#email", state="visible")
            page.fill("#email", usuario)
            page.fill("#password", password)
            page.locator(".row.submit button").click()
            page.wait_for_load_state("networkidle")
            print(f"{Fore.GREEN}[OK] Entry point reached")

            # OPEN COURSE
            print(f"{Fore.CYAN}[INFO] Opening course...")
            page.get_by_text("Variables, If Statements, Loops").wait_for()
            page.get_by_text("Variables, If Statements, Loops").click()
            page.wait_for_load_state("networkidle")
            print(f"{Fore.GREEN}[OK] Course opened")

            # CLICK CONTINUE
            continue_btn = page.locator('a:has(span:text("Continue"))')
            continue_btn.wait_for(state="visible")
            old_url = page.url
            continue_btn.click()
            page.wait_for_function("""(old) => window.location.href !== old""", arg=old_url, timeout=15000)
            print(f"{Fore.GREEN}[OK] Continue clicked")

            # MAIN LOOP: iterate lessons
            while True:
                contador+=1
                print(f"{Fore.MAGENTA}[INFO] COUT: {contador}")
                current_url = page.url
                print(f"{Fore.MAGENTA}[INFO] URL: {current_url}")
                time.sleep(2)

                match = re.search(r'#(\d+)\.', current_url)
                if not match:
                    print(f"{Fore.RED}[ERROR] Module not detected")
                    break
                
                module_number = match.group(1)
                print(f"{Fore.MAGENTA}[INFO] Module: {module_number}")

                filename = f"lesson_{module_number}.json"
                if os.path.exists(filename):
                    print(f"{Fore.MAGENTA}[INFO] JSON exists, reinstalling.")
                    os.remove(filename)

                print(f"{Fore.CYAN}[INFO] Downloading JSON...")
                response = page.context.request.get(
                    f"https://assets.codeavengers.com/file/docs/courses/py/1/es/{module_number}.json",
                    headers={"Referer": page.url, "Accept": "application/json"}
                )

                if response.ok:
                    lesson_data = response.json()
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(lesson_data, f, indent=4, ensure_ascii=False)
                    print(f"{Fore.GREEN}[OK] JSON saved: {filename}")
                else:
                    print(f"{Fore.RED}[ERROR] Status:", response.status)
                    print(response.text())
                    break

                # Wait for objective to render
                objective_header = page.locator("article.instructions.info.ca-content span.objective_text")
                page.wait_for_function(
                    "(el) => el.offsetHeight > 0 && el.innerText.length > 0",
                    arg=objective_header.element_handle(),
                    timeout=15000
                )

                objective_title = objective_header.inner_text().strip()
                print(f"{Fore.MAGENTA}[INFO] Objective: {objective_title}")

                # Fuzzy match objective in JSON
                target_objective = None
                for obj in lesson_data:
                    if es_similar(obj.get("objective", ""), objective_title, umbral=60):
                        target_objective = obj
                        break

                if target_objective:
                    goal = target_objective.get("goal", [])
                    print(f"{Fore.GREEN}[OK] Objective accepted.")
                    if find_button_run(goal):
                        print(f"{Fore.GREEN}[OK] [[#button,run]] found.")
                        flag = True
                        run_button = page.locator("#run-button")
                        run_button.click()
                        print(f"{Fore.GREEN}[INFO] Run clicked.")
                        time.sleep(1.5)
                    else:
                        print(f"{Fore.RED}[INFO] [[#button,run]] not found.")

                    solution_lines = target_objective.get("solution", [])
                    clean_lines = [line.strip() for line in solution_lines if isinstance(line, str) and line.strip()]
                    solution_code = "\n".join(clean_lines)


                    print(f"{Fore.WHITE}[SOLUTION]\n{solution_code}\n")
                    # Insert code in editor

                    editor_textarea = page.locator("#code-editor textarea.ace_text-input")
                    editor_textarea.wait_for(state="visible")
                    time.sleep(3)
                    page.evaluate("ace.edit('code-editor').setValue('');")
                    write_code_dynamically(page, solution_code)

                    if flag:
                        print(f"{Fore.GREEN}[INFO] Run clicked.")
                        run_button = page.locator("#run-button")
                        run_button.click()
                        time.sleep(2)
                        flag = False
                    print(f"{Fore.GREEN}[INFO] Verify clicked.")
                    verificar_btn = page.locator('button:has-text("Verificar")')
                    verificar_btn.wait_for(state="visible", timeout=10000)
                    verificar_btn.click()
                    page.wait_for_timeout(500)
                    time.sleep(2)
                    print(f"{Fore.GREEN}[INFO] Next clicked.")
                    siguiente_btn = page.locator('button#next-button')
                    siguiente_btn.wait_for(state="visible", timeout=10000)
                    siguiente_btn.click()
                    page.wait_for_timeout(2000)
                    page.wait_for_function("""(old) => window.location.href !== old""", arg=old_url, timeout=15000)
                else:
                    print(f"{Fore.RED}[ERROR] Objective not in JSON")
                    break

        finally:
            browser.close()

if __name__ == "__main__":
    main()
