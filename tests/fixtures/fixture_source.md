Источник: https://4pda.to/forum/index.php?showtopic=673847

Обновить слепок:

```python
import requests

url = "https://4pda.to/forum/index.php?showtopic=673847"
s = requests.Session()
s.headers["User-Agent"] = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
r = s.get(url, timeout=30)
r.raise_for_status()
open("tests/fixtures/4pda_thread_673847.html", "wb").write(r.content)
```
