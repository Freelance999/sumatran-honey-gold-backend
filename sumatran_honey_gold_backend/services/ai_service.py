import re
import json
from google import genai
from django.conf import settings

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