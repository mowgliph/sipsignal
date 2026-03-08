# cmc_api.py


import httpx

from bot.core.config import CMC_API_KEY_ALERTA, CMC_API_KEY_CONTROL


# === FUNCIONES DE API DE COINMARKETCAP ===
def _obtener_precios(monedas, api_key):
    """Función genérica y síncrona para obtener precios de CMC."""
    headers = {"X-CMC_PRO_API_KEY": api_key, "Accept": "application/json"}
    params = {"symbol": ",".join(monedas), "convert": "USD"}
    precios = {}
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            if not data or "data" not in data:
                return None if len(monedas) == 3 else {}

            for m in monedas:
                if m in data["data"]:
                    precios[m] = data["data"][m]["quote"]["USD"]["price"]

            return precios

    except httpx.HTTPError:
        return None if len(monedas) == 3 else {}


def obtener_precios_alerta():
    return _obtener_precios(["BTC", "TON", "HIVE", "HBD"], CMC_API_KEY_ALERTA)


def obtener_precios_control(monedas):
    return _obtener_precios(monedas, CMC_API_KEY_CONTROL)


def obtener_high_low_24h(moneda):
    """
    Obtiene el High y Low de las últimas 24h.
    Estrategia en cascada:
    1. Binance (Pares USDT, USDC)
    2. CryptoCompare (Universal, soporta HBD, HIVE, etc.)
    """
    symbol = moneda.upper()

    # --- INTENTO 1: BINANCE (Rápido y preciso) ---
    binance_pairs = [f"{symbol}USDT", f"{symbol}USDC"]
    for pair in binance_pairs:
        try:
            url = "https://api.binance.com/api/v3/ticker/24hr"
            with httpx.Client(timeout=2.0) as client:
                response = client.get(url, params={"symbol": pair})

                if response.status_code == 200:
                    data = response.json()
                    high = float(data.get("highPrice", 0))
                    low = float(data.get("lowPrice", 0))
                    if high > 0:
                        return high, low
        except Exception:
            pass  # Si falla, continuamos al siguiente intento

    # --- INTENTO 2: CRYPTOCOMPARE (El salvavidas universal) ---
    # Ideal para monedas que no estan en Binance (HBD, Altcoins raras)
    try:
        url_cc = "https://min-api.cryptocompare.com/data/pricemultifull"
        params_cc = {"fsyms": symbol, "tsyms": "USD"}
        # Timeout corto para no congelar el bot
        with httpx.Client(timeout=3.0) as client:
            response = client.get(url_cc, params=params_cc)
            data = response.json()

        # CryptoCompare devuelve una estructura RAW -> SYMBOL -> USD
        raw_data = data.get("RAW", {}).get(symbol, {}).get("USD", {})

        high = float(raw_data.get("HIGH24HOUR", 0))
        low = float(raw_data.get("LOW24HOUR", 0))

        return high, low

    except Exception as e:
        print(f"Error obteniendo High/Low fallback para {symbol}: {e}")
        return 0, 0


def _obtener_datos_cryptocompare(moneda):
    """
    Obtiene datos de una moneda desde CryptoCompare (fallback universal).
    Devuelve un diccionario con el mismo formato que CMC o None si falla.
    """
    symbol = moneda.upper()

    try:
        # Obtener datos de la moneda solicitada + ETH + BTC para conversiones
        url = "https://min-api.cryptocompare.com/data/pricemultifull"
        params = {"fsyms": f"{symbol},ETH,BTC", "tsyms": "USD"}

        with httpx.Client(timeout=5.0) as client:
            response = client.get(url, params=params)
            data = response.json()

        raw_data = data.get("RAW", {})

        # Verificar que tenemos datos para la moneda solicitada
        if symbol not in raw_data or "USD" not in raw_data[symbol]:
            return None

        symbol_data = raw_data[symbol]["USD"]
        eth_data = raw_data.get("ETH", {}).get("USD", {})
        btc_data = raw_data.get("BTC", {}).get("USD", {})

        price_usd = float(symbol_data.get("PRICE", 0))
        price_usd_eth = float(eth_data.get("PRICE", 0))
        price_usd_btc = float(btc_data.get("PRICE", 0))

        if price_usd == 0:
            return None

        # Calcular precios en ETH y BTC
        price_in_eth = price_usd / price_usd_eth if price_usd_eth != 0 else 0
        price_in_btc = price_usd / price_usd_btc if price_usd_btc != 0 else 0

        # CryptoCompare no tiene cambio 1h ni 7d en el endpoint gratuito
        change_24h = float(symbol_data.get("CHANGEPCT24HOUR", 0))

        return {
            "symbol": symbol,
            "price": price_usd,
            "price_eth": price_in_eth,
            "price_btc": price_in_btc,
            "high_24h": float(symbol_data.get("HIGH24HOUR", 0)),
            "low_24h": float(symbol_data.get("LOW24HOUR", 0)),
            "percent_change_1h": None,  # No disponible en CryptoCompare free
            "percent_change_24h": change_24h,
            "percent_change_7d": None,  # No disponible en CryptoCompare free
            "market_cap_rank": 0,  # No disponible en CryptoCompare
            "market_cap": float(symbol_data.get("MKTCAP", 0)),
            "volume_24h": float(symbol_data.get("VOLUME24HOUR", 0)),
        }

    except Exception as e:
        print(f"Error obteniendo datos de CryptoCompare para {symbol}: {e}")
        return None


def obtener_datos_moneda(moneda):
    """Obtiene datos detallados de una moneda. Intenta CMC primero, fallback a CryptoCompare."""
    symbol = moneda.upper()

    # === INTENTO 1: CoinMarketCap (datos más completos) ===
    try:
        headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY_CONTROL, "Accept": "application/json"}

        params = {"symbol": f"{symbol},ETH,BTC", "convert": "USD"}

        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
                headers=headers,
                params=params,
            )
            response.raise_for_status()

        full_data = response.json()["data"]

        # Verificar que tenemos todos los datos necesarios
        if symbol in full_data and "ETH" in full_data and "BTC" in full_data:
            data_moneda = full_data[symbol]
            data_eth = full_data["ETH"]
            data_btc = full_data["BTC"]

            quote_usd_moneda = data_moneda["quote"]["USD"]
            price_usd_eth = data_eth["quote"]["USD"]["price"]
            price_usd_btc = data_btc["quote"]["USD"]["price"]

            price_in_eth = quote_usd_moneda["price"] / price_usd_eth if price_usd_eth != 0 else 0
            price_in_btc = quote_usd_moneda["price"] / price_usd_btc if price_usd_btc != 0 else 0

            # Obtener high/low de Binance/CryptoCompare
            hl_high, hl_low = obtener_high_low_24h(symbol)

            return {
                "symbol": data_moneda["symbol"],
                "price": quote_usd_moneda["price"],
                "price_eth": price_in_eth,
                "price_btc": price_in_btc,
                "high_24h": hl_high,
                "low_24h": hl_low,
                "percent_change_1h": quote_usd_moneda["percent_change_1h"],
                "percent_change_24h": quote_usd_moneda["percent_change_24h"],
                "percent_change_7d": quote_usd_moneda["percent_change_7d"],
                "market_cap_rank": data_moneda["cmc_rank"],
                "market_cap": quote_usd_moneda["market_cap"],
                "volume_24h": quote_usd_moneda["volume_24h"],
            }

    except Exception as e:
        print(f"CMC falló para {symbol}, intentando fallback: {e}")

    # === INTENTO 2: CryptoCompare (fallback universal) ===
    print(f"Usando fallback CryptoCompare para {symbol}")
    return _obtener_datos_cryptocompare(symbol)
