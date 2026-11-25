from Core.api.client import BrainClient

def get_day1_universe_map(client: BrainClient, instrument_type="EQUITY") -> dict:
    """
    动态请求 WorldQuant BRAIN 接口，返回所有合法的 Region 及其对应的 Universe 列表。
    """
    try:
        response = client.options('/simulations')
        if not response or response.status_code != 200:
            print(f"Failed to fetch options, status code: {response.status_code if response else 'None'}")
            return {}
            
        data = response.json()
        settings_options = data.get('actions', {}).get('POST', {}).get('settings', {}).get('children', {})
        
        universe_data = {}
        for key, setting in settings_options.items():
            if setting.get('type') == 'choice' and (setting.get('label') == 'Universe' or key == 'universe'):
                universe_data = setting.get('choices', {}).get('instrumentType', {}).get(instrument_type, {})
                break
                
        regions_dict = universe_data.get('region', {})
        result_map = {}
        
        for region, items in regions_dict.items():
            universes = [item.get('value') for item in items if item.get('value')]
            if universes:
                result_map[region] = universes
                
        return result_map
    except Exception as e:
        print(f"Error dynamically fetching scopes: {e}")
        return {}

def get_all_valid_scopes(client: BrainClient, instrument_type="EQUITY") -> list:
    """
    返回所有的 (region, universe) 元组列表。
    """
    day1_map = get_day1_universe_map(client, instrument_type)
    scopes = []
    for region, universes in day1_map.items():
        for universe in universes:
            scopes.append((region, universe))
    return scopes
