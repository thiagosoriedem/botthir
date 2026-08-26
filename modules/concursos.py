import re
from bs4 import BeautifulSoup
import requests

REGION_URL = "https://www.pciconcursos.com.br/concursos/nordeste/"


def fetch_pci_jobs(filtro_estado=""):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(REGION_URL, headers=headers, timeout=10)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.content, "html.parser")
        concursos = []
        sigla_alvo = filtro_estado.upper().strip() if filtro_estado else ""

        for item in soup.select(".ca"):
            link_elem = item.select_one("a")
            if not link_elem:
                continue

            cc_elem = item.select_one(".cc")
            estado_sigla = cc_elem.text.strip().upper() if cc_elem else ""

            if (
                sigla_alvo
                and sigla_alvo != "ALL"
                and estado_sigla != sigla_alvo
            ):
                continue

            titulo = link_elem.text.strip()
            link = link_elem["href"]
            if link.startswith("/"):
                link = f"https://www.pciconcursos.com.br{link}"

            cd_text = (
                item.select_one(".cd").text.strip()
                if item.select_one(".cd")
                else ""
            )
            ce_text = (
                item.select_one(".ce").text.strip()
                if item.select_one(".ce")
                else ""
            )

            data_limite = "N/A"
            vagas_detalhes = ""

            if re.search(r"\d{2}/\d{2}/\d{4}", cd_text):
                data_limite = cd_text
                vagas_detalhes = ce_text
            elif re.search(r"\d{2}/\d{2}/\d{4}", ce_text):
                data_limite = ce_text
                vagas_detalhes = cd_text
            else:
                vagas_detalhes = f"{cd_text} {ce_text}".strip()

            nivel = "N/A"
            for n in [
                "Superior",
                "Técnico",
                "Médio",
                "Fundamental",
                "Alfabetizado",
            ]:
                if n.lower() in vagas_detalhes.lower():
                    nivel = n
                    vagas_detalhes = re.sub(
                        rf"\b{n}\b", "", vagas_detalhes, flags=re.IGNORECASE
                    ).strip()
                    break

            card = (
                f"🏛️ *{titulo}* [{estado_sigla}]\n"
                f"🎓 *Nível:* {nivel}\n"
                f"💰 *Vagas / Cargo:* {vagas_detalhes}\n"
                f"⏳ *Inscrições até:* {data_limite}\n"
                f"🔗 [Acessar Edital/Notícia]({link})"
            )
            concursos.append(card)

        return concursos
    except Exception as e:
        print(f"Erro no scraping de concursos: {e}")
        return []


def get_concursos_state_keyboard():
    """Teclado de seleção de estados para concursos."""
    return {
        "inline_keyboard": [
            [
                {"text": "🌵 Paraíba (PB)", "callback_data": "page_PB_0"},
                {"text": "🌊 Pernambuco (PE)", "callback_data": "page_PE_0"},
            ],
            [
                {"text": "☀️ Ceará (CE)", "callback_data": "page_CE_0"},
                {"text": "🌴 Rio Grande do Norte (RN)", "callback_data": "page_RN_0"},
            ],
            [
                {"text": "🌐 Ver Todos (Nordeste)", "callback_data": "page_ALL_0"}
            ],
            [{"text": "🏠 Voltar ao Menu Principal", "callback_data": "main_menu"}],
        ]
    }


def get_concursos_pagination_keyboard(sigla, next_offset, total_items):
    """Teclado de paginação para concursos."""
    buttons = []
    if next_offset < total_items:
        buttons.append([
            {
                "text": f"➕ Carregar Mais ({next_offset}/{total_items})",
                "callback_data": f"page_{sigla}_{next_offset}",
            }
        ])
    buttons.append([{"text": "🔙 Voltar a Estados", "callback_data": "menu_concursos"}])
    buttons.append([{"text": "🏠 Menu Principal", "callback_data": "main_menu"}])
    return {"inline_keyboard": buttons}