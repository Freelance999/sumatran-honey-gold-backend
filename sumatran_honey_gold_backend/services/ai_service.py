import re
import json
from google import genai
from django.conf import settings
from typing import Optional, Dict, Any

client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

class AiService:
    @staticmethod
    def build_prompt(weather, live, batches):
        return f"""
        Anda adalah AI monitoring pertanian untuk produksi madu.

        Analisa data berikut dan buatkan system alerts.

        ATURAN KETAT:
        - Output HARUS berupa JSON valid
        - TANPA markdown
        - TANPA penjelasan tambahan
        - HANYA array JSON

        - Maksimal 5 alert
        - Jika tidak ada masalah, tetap buat 1 alert dengan level "info"

        FORMAT:
        [
        {{
            "level": "info | warning | critical",
            "title": "string (Bahasa Indonesia)",
            "message": "string (Bahasa Indonesia)",
            "recommendation": "string (Bahasa Indonesia)"
        }}
        ]

        FOKUS:
        - anomali cuaca
        - risiko panen
        - masalah produksi

        DATA:

        WEATHER:
        {weather}

        LIVE:
        {live}

        BATCHES:
        {batches}
        """
    
    @staticmethod
    def generate_alerts(prompt: str):
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        text = response.text

        try:
            return json.loads(text)
        except:
            match = re.search(r"\[.*\]", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass

            return []
        
    @staticmethod
    def generate_rule_based_alerts(weather, live, batches):
        alerts = []

        if not weather:
            alerts.append({
                "level": "warning",
                "title": "Data Cuaca Tidak Tersedia",
                "message": "Tidak ada data cuaca dalam 24 jam terakhir",
                "recommendation": "Periksa sensor atau koneksi perangkat"
            })

        if live.get("status") == "STOPPED":
            alerts.append({
                "level": "critical",
                "title": "Proses Panen Berhenti",
                "message": "Aktivitas panen saat ini dalam kondisi berhenti",
                "recommendation": "Segera lakukan pengecekan lapangan"
            })

        if live.get("temperature") and live["temperature"] > 34:
            alerts.append({
                "level": "warning",
                "title": "Suhu Tinggi Saat Panen",
                "message": f"Suhu mencapai {live['temperature']}°C",
                "recommendation": "Pertimbangkan penyesuaian waktu panen"
            })

        if live.get("humidity") and live["humidity"] > 70:
            alerts.append({
                "level": "warning",
                "title": "Kelembaban Tinggi",
                "message": f"Kelembaban mencapai {live['humidity']}%",
                "recommendation": "Pastikan penyimpanan madu optimal"
            })

        bad_batches = [b for b in batches if b["status"] != "GOOD"]
        if len(bad_batches) > 5:
            alerts.append({
                "level": "warning",
                "title": "Banyak Batch Bermasalah",
                "message": f"{len(bad_batches)} batch memiliki status tidak normal",
                "recommendation": "Evaluasi kualitas produksi"
            })

        return alerts

    @staticmethod
    def build_mentor_analysis_prompt(statistics: dict) -> str:
        return f"""
        Anda adalah asisten analitik untuk dashboard mentor penjualan madu.

        Tugas: berikan 3 ringkasan naratif singkat dalam Bahasa Indonesia berdasarkan data JSON berikut.
        Satu paragraf per area; gaya profesional, positif, dan actionable.

        ATURAN KETAT:
        - Output HARUS berupa JSON valid
        - TANPA markdown
        - TANPA penjelasan di luar JSON
        - HANYA objek JSON dengan tepat 3 key berikut (string values):

        FORMAT:
        {{
        "mentor_commission": "string",
        "mentor_income": "string",
        "mentor_network": "string"
        }}

        DATA STATISTIK:
        {json.dumps(statistics, ensure_ascii=False)}
        """

    @staticmethod
    def _parse_json_object(text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            pass
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return None
        return None

    @staticmethod
    def analyze_mentor_statistics(statistics: dict) -> dict:
        fallback = {
            "mentor_commission": "Analisis komisi mentor tidak dapat dihasilkan saat ini.",
            "mentor_income": "Analisis penjualan pribadi tidak dapat dihasilkan saat ini.",
            "mentor_network": "Analisis jaringan tidak dapat dihasilkan saat ini.",
        }
        try:
            prompt = AiService.build_mentor_analysis_prompt(statistics)
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            text = response.text
        except Exception:
            return fallback

        parsed = AiService._parse_json_object(text)
        if not isinstance(parsed, dict):
            return fallback

        for key in ("mentor_commission", "mentor_income", "mentor_network"):
            if key not in parsed or not isinstance(parsed[key], str):
                parsed[key] = fallback[key]
        return parsed