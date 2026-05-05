import sys
import os
import json
import time
import re
from fuzzywuzzy import fuzz
from colorama import init, Fore
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

init(autoreset=True)

# ---------------------- FUNCIONES AUXILIARES ----------------------
def limpiar_texto(texto):
    """Elimina variables tipo {{variable}} del texto."""
    return re.sub(r"\{\{.*?\}\}", "", texto)

def es_similar(texto1, texto2, umbral=60):
    """Compara dos textos y devuelve True si la similitud supera el umbral."""
    texto1_limpio = limpiar_texto(texto1)
    texto2_limpio = limpiar_texto(texto2)
    similitud = fuzz.ratio(texto1_limpio, texto2_limpio)
    print(f"Similarity: {similitud}%")
    return similitud >= umbral

def print_progress_bar(percent):
    """Barra de progreso para escritura de código."""
    bar_length = 20
    block = int(round(bar_length * percent))
    progress = "#" * block + "-" * (bar_length - block)
    print(f"\r[{progress}] {percent*100:.0f}%", end="", flush=True)

def limpiar_codigo_completo(code):
    """Elimina comillas tipográficas, tabs y todos los caracteres invisibles Unicode."""
    code = code.replace('“','"').replace('”','"')
    code = code.replace('‘',"'").replace('’',"'")
    code = code.replace('\t','    ')
    # Eliminar todos los caracteres invisibles excepto saltos de línea
    code = ''.join(c for c in code if c.isprintable() or c=='\n')
    return code

def write_code_dynamically(page, code):
    """Escribe el código limpio en el editor de CodeAvengers línea por línea."""
    code = limpiar_codigo_completo(code)
    editor_textarea = page.locator("#code-editor textarea.ace_text-input")
    editor_textarea.wait_for(state="visible")
    # Borrar completamente el editor
    page.evaluate("ace.edit('code-editor').setValue('');")
    time.sleep(0.5)
    
    lines = code.splitlines()
    for i, line in enumerate(lines):
        page.type("#code-editor textarea.ace_text-input", line)
        page.keyboard.press("Enter")
        print_progress_bar(i / len(lines))
    print("\n")
    print(f"{Fore.WHITE}[INFO] Code written.\n")
    return True

def launch_browser(playwright):
    """Lanza el navegador Chromium con Playwright."""
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    return browser, page

def increment_last_number_in_url(url):
    """Incrementa en 1 el último número de la URL (ej. #11.2 -> #11.3)."""
    match = re.search(r'(\d+)(?=[^0-9]*$)', url)
    if match:
        last_num = int(match.group(1))
        new_num = last_num + 1
        new_url = url[:match.start(1)] + str(new_num) + url[match.end(1):]
        print(f"{Fore.CYAN}[URL] {url} -> {new_url}")
        return new_url
    return url

def is_review_quiz_present(page):
    """Detecta si hay un 'Review Quiz' listo usando el div específico."""
    try:
        quiz_div = page.locator('div.js.review-game_objective:has-text("Review Quiz")')
        return quiz_div.count() > 0 and quiz_div.is_visible()
    except:
        return False

def handle_review_quiz(page):
    """Si existe un Review Quiz, intenta avanzar. Primero incrementa el decimal. Si no funciona, salta al siguiente entero."""
    if is_review_quiz_present(page):
        print(f"{Fore.CYAN}[INFO] Review Quiz detectado")
        old_url = page.url
        time.sleep(3)
        if page.url == old_url:
            # Intentar incrementar decimal
            match = re.search(r'(\d+)(?=[^0-9]*$)', page.url)
            if match:
                last_num = int(match.group(1))
                new_num = last_num + 1
                new_url = page.url[:match.start(1)] + str(new_num) + page.url[match.end(1):]
                print(f"{Fore.CYAN}[INFO] Intentando navegar a {new_url}")
                page.goto(new_url)
                page.wait_for_load_state("networkidle")
                time.sleep(2)
                # Si después de navegar, el Review Quiz sigue presente o la URL no cambió (redirección), entonces saltar al entero
                if is_review_quiz_present(page) or page.url == old_url:
                    print(f"{Fore.YELLOW}[INFO] La página {new_url} no es válida, saltando al siguiente entero")
                    # Calcular siguiente entero: extraer parte entera actual
                    match_entero = re.search(r'#(\d+)\.', old_url)
                    if match_entero:
                        entero_actual = int(match_entero.group(1))
                        nuevo_entero = entero_actual + 1
                        # Reemplazar el número entero en la URL y poner .1 al final
                        nueva_url_entero = re.sub(r'#\d+\.', f'#{nuevo_entero}.', old_url)
                        # Pero cuidado: puede haber más números después del punto. Asumimos que el formato es #XX.Y
                        # Mejor: construir nueva URL con el entero incrementado y .1
                        # Ejemplo: #11.5 -> #12.1
                        base_url = old_url.split('#')[0]
                        nueva_url_entero = f"{base_url}#{nuevo_entero}.1"
                        print(f"{Fore.CYAN}[INFO] Navegando a {nueva_url_entero}")
                        page.goto(nueva_url_entero)
                        page.wait_for_load_state("networkidle")
                        return True
        return False

def handle_dialog(dialog):
    """Manejador global para diálogos (alert, confirm, prompt)."""
    print(f"{Fore.YELLOW}[DIALOG] Tipo: {dialog.type}, mensaje: {dialog.message}")
    if dialog.type == "prompt":
        dialog.accept("Estudiante")   # Respuesta genérica para input()
    else:
        dialog.accept()

# ---------------------- FUNCIÓN PRINCIPAL ----------------------
def main():
    contador = 0
    print(f"{Fore.CYAN}[INFO] Iniciando...")

    with open("config.json") as f:
        data = json.load(f)

    usuario = input("Email: ")
    password = input("Password: ")

    with sync_playwright() as p:
        browser, page = launch_browser(p)
        page.on('dialog', handle_dialog)   # Manejador de diálogos (prompt)

        try:
            # LOGIN
            print(f"{Fore.CYAN}[INFO] Logging in...")
            page.goto("https://www.codeavengers.com", wait_until="networkidle")
            page.locator("header").get_by_role("link", name="Log in").click()
            page.wait_for_selector("#email", state="visible")
            page.fill("#email", usuario)
            page.fill("#password", password)
            page.locator(".row.submit button").click()
            page.wait_for_load_state("networkidle")
            print(f"{Fore.GREEN}[OK] Entry point reached")

            # ABRIR CURSO
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

            # BUCLE PRINCIPAL
            while True:
                contador += 1
                print(f"{Fore.MAGENTA}[INFO] Ciclo #{contador}")
                current_url = page.url
                print(f"{Fore.MAGENTA}[INFO] URL: {current_url}")
                time.sleep(2)

                match = re.search(r'#(\d+)\.', current_url)
                if not match:
                    print(f"{Fore.RED}[ERROR] No se detectó módulo en la URL")
                    break
                module_number = match.group(1)
                print(f"{Fore.MAGENTA}[INFO] Módulo: {module_number}")

                # Descargar JSON de la lección
                filename = f"lesson_{module_number}.json"
                if os.path.exists(filename):
                    os.remove(filename)

                print(f"{Fore.CYAN}[INFO] Descargando JSON...")
                response = page.context.request.get(
                    f"https://assets.codeavengers.com/file/docs/courses/py/1/es/{module_number}.json",
                    headers={"Referer": page.url, "Accept": "application/json"}
                )
                if response.ok:
                    lesson_data = response.json()
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(lesson_data, f, indent=4, ensure_ascii=False)
                    print(f"{Fore.GREEN}[OK] JSON guardado: {filename}")
                else:
                    print(f"{Fore.RED}[ERROR] Status: {response.status}")
                    break

                try:
                    objective_header = page.locator("article.instructions.info.ca-content span.objective_text")
                    page.wait_for_function(
                        "(el) => el.offsetHeight > 0 && el.innerText.length > 0",
                        arg=objective_header.element_handle(),
                        timeout=15000
                    )
                    objective_title = objective_header.inner_text().strip()
                except:
                    print(f"{Fore.YELLOW}[INFO] No se encontró objetivo...")
                    objective_title = ""

                print(f"{Fore.MAGENTA}[INFO] Objetivo: {objective_title}")

                if handle_review_quiz(page):
                    continue

                target_objective = None
                for obj in lesson_data:
                    if es_similar(obj.get("objective", ""), objective_title, umbral=60):
                        target_objective = obj
                        break

                if not target_objective:
                    print(f"{Fore.RED}[ERROR] Objetivo no encontrado en JSON")
                    break

                goal = target_objective.get("goal", [])
                solution_lines = target_objective.get("solution", [])
                clean_lines = [line.strip() for line in solution_lines if isinstance(line, str) and line.strip()]
                solution_code = "\n".join(clean_lines)
                print(f"{Fore.WHITE}[SOLUTION]\n{solution_code}\n")

                # Insertar código limpio
                write_code_dynamically(page, solution_code)

                # Verificar
                print(f"{Fore.GREEN}[INFO] Haciendo clic en Verificar...")
                verificar_btn = page.locator('button:has-text("Verificar")')
                verificar_btn.wait_for(state="visible", timeout=10000)
                verificar_btn.click()
                page.wait_for_timeout(2000)

                error_span = page.query_selector('span.js.message-bar_text:has-text("Inténtalo de nuevo")')
                if error_span and error_span.is_visible():
                    print(f"{Fore.RED}[ERROR] Se detectó 'Inténtalo de nuevo'")
                    new_url = increment_last_number_in_url(page.url)
                    print(f"{Fore.CYAN}[INFO] Navegando a {new_url}")
                    page.goto(new_url)
                    page.wait_for_load_state("networkidle")
                    continue

                # Siguiente tarea
                print(f"{Fore.GREEN}[INFO] Haciendo clic en Siguiente...")
                siguiente_btn = page.locator('button#next-button')
                siguiente_btn.wait_for(state="visible", timeout=10000)
                siguiente_btn.click()
                page.wait_for_timeout(2000)
                page.wait_for_function("""(old) => window.location.href !== old""", arg=old_url, timeout=15000)
                time.sleep(2)

                if handle_review_quiz(page):
                    continue

        finally:
            browser.close()

if __name__ == "__main__":
    main()

