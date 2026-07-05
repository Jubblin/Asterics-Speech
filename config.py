import os

import provider_piper_data

speechProviderList = [provider_piper_data]
cacheData = os.environ["CACHE_DATA"].lower() in ("1", "true", "yes")
