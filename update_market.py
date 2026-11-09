import json, os, datetime, math
import yfinance as yf

SYMBOLS={'KOSPI':'^KS11','KOSDAQ':'^KQ11','NASDAQ':'^IXIC','NYSE':'^NYA'}
OUT='market.json'
try:
    with open(OUT,encoding='utf-8') as f: existing=json.load(f)
except Exception: existing={'markets':{}}
markets={}
for name,ticker in SYMBOLS.items():
    try:
        t=yf.Ticker(ticker)
        daily=t.history(period='5y',interval='1d',auto_adjust=False)
        intra=t.history(period='5d',interval='15m',auto_adjust=False)
        if daily.empty: raise ValueError('No daily data')
        def series(df):
            out=[]
            for ts,row in df.iterrows():
                v=float(row['Close'])
                if math.isfinite(v) and v>0:
                    out.append([ts.isoformat(),round(v,3)])
            return out
        d=series(daily)
        i=series(intra) if not intra.empty else []
        last=i[-1][1] if i else d[-1][1]
        prev=d[-2][1] if len(d)>1 else last
        # If last intraday session is after the latest daily close, compare to daily close;
        # otherwise compare the last available daily close to the preceding close.
        if i and i[-1][0][:10]>d[-1][0][:10]: prev=d[-1][1]
        pct=(last/prev-1)*100 if prev else 0
        markets[name]={'symbol':ticker,'price':last,'change':round(last-prev,3),'changePct':round(pct,3),'daily':d,'intraday':i,'asof':(i[-1][0] if i else d[-1][0]),'status':'ok'}
        print(name,len(d),len(i),last)
    except Exception as exc:
        print('WARNING',name,str(exc))
        old=existing.get('markets',{}).get(name)
        if old:
            old['status']='stale'
            markets[name]=old
        else:
            markets[name]={'symbol':ticker,'status':'unavailable','daily':[],'intraday':[]}
result={'updatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'markets':markets}
with open(OUT,'w',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,separators=(',',':'))
