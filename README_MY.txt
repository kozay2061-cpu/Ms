AI MUSIC STUDIO V2.2 — ONLINE STARTER PROJECT

ပါဝင်သောဖိုင်များ
- online.html: server API ကိုခေါ်သုံးသည့် website
- app.py: Flask backend, audio analysis endpoint
- requirements.txt: Python package များ
- browser_demo.html: backend မလိုဘဲ browser ထဲတွင် စမ်းနိုင်သော prototype

အရေးကြီး
ဒီ project သည် အမှန်တကယ် cloud AI model မဟုတ်သေးပါ။ Online.html သည် app.py ကို server ပေါ်တွင် run ထားသောအခါ API ကိုခေါ်ပြီး librosa signal-processing ခွဲခြမ်းစိတ်ဖြာမှု လုပ်ပေးသည်။ Style သည် BPM အပေါ် အခြေခံသည့် အကြမ်းဖျင်းခန့်မှန်းချက်သာဖြစ်သည်။ Time signature ကို ယုံကြည်စိတ်ချရစွာ အလိုအလျောက်မသိနိုင်သဖြင့် manual ဖြစ်သည်။ Chord/Key လည်း မှားနိုင်သည်။

စမ်းသပ်ရန် (ကွန်ပျူတာတွင် Python တပ်ဆင်ထားရန်လို)
1. Project folder ထဲတွင် terminal/cmd ဖွင့်ပါ။
2. python -m venv .venv
3. Windows: .venv\\Scripts\\activate  | Mac/Linux: source .venv/bin/activate
4. pip install -r requirements.txt
5. python app.py
6. Browser မှ http://127.0.0.1:5000 ကိုဖွင့်ပါ။

အွန်လိုင်းတကယ်တင်ရန်
- Flask app ကို Python support ရှိသော hosting ပေါ် deploy လုပ်ရမည်။
- HTTPS သုံးပါ၊ upload limit နှင့် timeout ကို စီမံပါ။
- app.py ၏ host ကို 0.0.0.0 ပြောင်းပြီး production WSGI server (ဥပမာ gunicorn) သုံးရမည်။
- ဒီ local test server ကို public internet သို့ တိုက်ရိုက်မဖွင့်ပါနှင့်။
- Public AI API/hosting key များကို HTML ထဲမထည့်ပါနှင့်။

လက်ရှိ backend လုပ်ဆောင်ချက်
- BPM / beat positions: librosa beat tracker
- Key: chroma profile + major/minor profile comparison
- Chord: major/minor/diminished triad template matching
- Bars: duration × BPM / 60 / 4 (4/4 အကြမ်းဖျင်း)
- Style: tempo-based heuristic; actual genre classifier မဟုတ်
