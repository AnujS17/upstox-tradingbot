
base_url = "https://api.upstox.com/v2"
access_token = ""
client_id = ""
sector_params = {
            # Technology
                    
            "Technology": {"debt_equity_max": 0.5, "pe_max": 35, "interest_coverage": 5},
            "Software": {"debt_equity_max": 0.6, "pe_max": 50, "interest_coverage": 4},
            "Semiconductors": {"debt_equity_max": 0.7, "pe_max": 30, "interest_coverage": 4},
            
            "Banking": {"debt_equity_max": 10, "pe_max": 15, "interest_coverage": 1.5},
            "Financial Services": {"debt_equity_max": 3, "pe_max": 30, "interest_coverage": 2.5},
            "Insurance": {"debt_equity_max": 0.9, "pe_max": 18, "interest_coverage": 3},
            
            "Pharmaceuticals": {"debt_equity_max": 0.8, "pe_max": 25, "interest_coverage": 6},
            "Biotechnology": {"debt_equity_max": 1.0, "pe_max": 50, "interest_coverage": 2},
            "Healthcare": {"debt_equity_max": 0.7, "pe_max": 30, "interest_coverage": 4},
            
            "Automobile": {"debt_equity_max": 1.5, "pe_max": 12, "interest_coverage": 3},
            "Consumer Durables": {"debt_equity_max": 1.0, "pe_max": 20, "interest_coverage": 4},
            "Retail": {"debt_equity_max": 1.2, "pe_max": 18, "interest_coverage": 3},
            
            "Construction": {"debt_equity_max": 2.0, "pe_max": 10, "interest_coverage": 2},
            "Metals & Mining": {"debt_equity_max": 1.8, "pe_max": 8, "interest_coverage": 2.5},
            "Oil & Gas": {"debt_equity_max": 1.5, "pe_max": 10, "interest_coverage": 3},
            
            "Utilities": {"debt_equity_max": 2.5, "pe_max": 18, "interest_coverage": 2},
            "Telecom": {"debt_equity_max": 2.2, "pe_max": 15, "interest_coverage": 2},
            "FMCG": {"debt_equity_max": 0.8, "pe_max": 25, "interest_coverage": 5},
            
            "default": {"debt_equity_max": 0.8, "pe_max": 25, "interest_coverage": 3}
        }
SYMBOL_TO_ISIN = {
        "RELIANCE": "INE002A01018",
        "TATASTEEL": "INE081A01012",
        "HDFCBANK": "INE040A01034",
        "INFY": "INE009A01021",
        "BHARTIARTL": "INE397D01024",
        "VODAFONE IDEA": "INE669E01016",
        "ICICIBANK": "INE090A01021"
    }