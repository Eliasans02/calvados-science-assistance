"""Scraper for adilet.zan.kz - Kazakhstan legal database."""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import List, Dict, Optional
from datetime import datetime
import sys
import os
sys.path.append(str(os.path.dirname(os.path.dirname(__file__))))
from config import ADILET_BASE_URL, SCRAPE_DELAY, RAW_DATA_DIR


class AdiletScraper:
    """Scraper for Kazakhstan legal documents from adilet.zan.kz"""
    
    def __init__(self, base_url: str = ADILET_BASE_URL):
        self.base_url = base_url
        self.delay = SCRAPE_DELAY
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def search_documents(self, query: str = "", doc_type: str = "",
                        year_from: int = 1991, year_to: int = 2035,
                        limit: int = 50, max_pages: int = 10) -> List[Dict]:
        """
        Search for documents on adilet.zan.kz
        
        Args:
            query: Search query
            doc_type: Type of document (закон, указ, etc.)
            year_from: Start year
            year_to: End year
            limit: Maximum number of documents
            
        Returns:
            List of document metadata
        """
        documents = []
        seen_urls = set()
        
        print(f"Searching adilet.zan.kz: query='{query}', years={year_from}-{year_to}")
        
        try:
            search_url = f"{self.base_url}/rus/search/docs"
            
            params = {
                'q': query,
                'sort_field': 'dt',
                'sort_desc': 'true'
            }
            
            print(f"GET {search_url} with params: {params}")
            
            response = self.session.get(search_url, params=params, timeout=10)

            if response.status_code != 200:
                print(f"Search returned status {response.status_code}")
                raise Exception(f"HTTP {response.status_code}")

            soup = BeautifulSoup(response.content, 'html.parser')
            self._collect_documents_from_soup(
                soup=soup,
                documents=documents,
                seen_urls=seen_urls,
                year_from=year_from,
                year_to=year_to,
                limit=limit
            )

            if len(documents) < limit:
                page_links = self._extract_page_links(soup)
                for page_url in page_links[:max_pages - 1]:
                    if len(documents) >= limit:
                        break
                    try:
                        time.sleep(self.delay)
                        page_response = self.session.get(
                            page_url,
                            params=params,
                            timeout=10
                        )
                        if page_response.status_code != 200:
                            continue
                        page_soup = BeautifulSoup(page_response.content, 'html.parser')
                        self._collect_documents_from_soup(
                            soup=page_soup,
                            documents=documents,
                            seen_urls=seen_urls,
                            year_from=year_from,
                            year_to=year_to,
                            limit=limit
                        )
                    except Exception:
                        continue

            print(f"Found {len(documents)} documents from adilet.zan.kz")
                
        except Exception as e:
            print(f"Real scraping failed: {e}")
            documents = []
        
        return documents

    def _extract_page_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract pagination links."""
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/rus/search/docs/page=' not in href:
                continue
            full = href if href.startswith('http') else f"{self.base_url}{href}"
            links.add(full)

        def page_key(url: str) -> int:
            m = re.search(r'/page=(\d+)', url)
            return int(m.group(1)) if m else 10**9

        return sorted(links, key=page_key)

    def _collect_documents_from_soup(
        self,
        soup: BeautifulSoup,
        documents: List[Dict],
        seen_urls: set,
        year_from: int,
        year_to: int,
        limit: int
    ) -> None:
        """Collect and normalize documents from a search results page."""
        post_holders = soup.find_all('div', class_='post_holder')

        for idx, holder in enumerate(post_holders):
            if len(documents) >= limit:
                return

            a_tag = holder.find('a', href=lambda x: x and '/rus/docs/' in x)
            if not a_tag:
                continue

            href = a_tag.get('href', '').strip()
            if not href:
                continue
            url = href if href.startswith('http') else f"{self.base_url}{href}"
            if url in seen_urls:
                continue

            title = " ".join(a_tag.get_text(" ", strip=True).split())
            meta_text = " ".join(holder.get_text(" ", strip=True).split())

            date_match = re.search(
                r'(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\s+[а-яА-Я]+\s+\d{4}\s+года)',
                meta_text
            )
            date_value = date_match.group(1) if date_match else "Дата неизвестна"

            year_match = re.search(r'(\d{4})', date_value)
            if year_match:
                y = int(year_match.group(1))
                if y < year_from or y > year_to:
                    continue

            status_value = "Неизвестно"
            low_meta = meta_text.lower()
            if "утратив" in low_meta:
                status_value = "Утратил силу"
            elif "действующ" in low_meta:
                status_value = "Действующий"
            elif "новый" in low_meta:
                status_value = "Новый"

            doc_id = url.rstrip('/').split('/')[-1] or f"doc_{idx}"
            documents.append({
                "id": doc_id,
                "title": title or "Без названия",
                "url": url,
                "date": date_value,
                "status": status_value,
                "type": "Документ",
                "scraped_at": datetime.now().isoformat()
            })
            seen_urls.add(url)
    
    def fetch_document(self, url: str) -> Optional[Dict]:
        """
        Fetch full document text from URL.
        
        Args:
            url: Document URL
            
        Returns:
            Document data with full text
        """
        try:
            print(f"Fetching: {url}")
            time.sleep(self.delay)
            
            # Реальный парсинг страницы
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Ищем текст документа по разным селекторам
                full_text = ""
                
                # Вариант 1: Основной контент в div.document-content
                content_div = soup.find('div', class_='document-content') or \
                             soup.find('div', class_='doc-content') or \
                             soup.find('div', id='document') or \
                             soup.find('article')
                
                if content_div:
                    full_text = content_div.get_text(separator='\n', strip=True)
                else:
                    # Вариант 2: Весь body если специфичного контейнера нет
                    body = soup.find('body')
                    if body:
                        # Убираем навигацию, меню, футер
                        for tag in body.find_all(['nav', 'header', 'footer', 'script', 'style']):
                            tag.decompose()
                        full_text = body.get_text(separator='\n', strip=True)
                
                # Извлекаем метаданные
                title = soup.find('h1')
                title_text = title.get_text(strip=True) if title else "Без названия"
                
                # Если текст получили
                if full_text and len(full_text) > 100:
                    return {
                        "url": url,
                        "title": title_text,
                        "full_text": full_text,
                        "fetched_at": datetime.now().isoformat(),
                        "word_count": len(full_text.split()),
                        "source": "real"
                    }
                else:
                    print(f"Insufficient text extracted ({len(full_text)} chars)")
                    return None
            else:
                print(f"HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Real fetching failed: {e}")
            return None
    
    def save_documents(self, documents: List[Dict], filename: str = "documents.json"):
        """Save documents to JSON file."""
        filepath = RAW_DATA_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Saved {len(documents)} documents to {filepath}")
        return filepath


# Test
if __name__ == "__main__":
    scraper = AdiletScraper()
    
    # Search documents
    docs = scraper.search_documents(query="министерство", limit=5)
    
    # Fetch full text for first document
    if docs:
        full_doc = scraper.fetch_document(docs[0]['url'])
        if full_doc:
            docs[0].update(full_doc)
    
    # Save
    scraper.save_documents(docs)
    print("\n✅ Scraper test complete!")
