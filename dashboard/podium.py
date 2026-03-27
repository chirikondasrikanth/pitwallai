"""
dashboard/podium.py  —  PitWall AI Cinematic UI  v3
Full-screen hero carousel + prediction overlay.
Apple / Netflix / F1 broadcast aesthetic.
"""
import os, sys

_DASH = os.path.dirname(os.path.abspath(__file__))
_BASE = os.path.dirname(_DASH)
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

try:
    from src.f1_assets import CIRCUIT_BACKGROUNDS, DRIVER_DATA, DEFAULT_BG, get_circuit_bg
except ImportError:
    CIRCUIT_BACKGROUNDS = {}
    DRIVER_DATA = {}
    DEFAULT_BG = "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1920&q=90"
    def get_circuit_bg(c): return DEFAULT_BG  # noqa

# ─── Teams / Drivers ──────────────────────────────────────────────────────────

TC = {
    "Mercedes":"#27F4D2","Ferrari":"#E8002D","McLaren":"#FF8000","Red Bull":"#3671C6",
    "Aston Martin":"#229971","Alpine":"#FF87BC","Haas":"#B6BABD","Racing Bulls":"#6692FF",
    "Williams":"#37BEDD","Audi":"#888888","Cadillac":"#CCCCCC",
}

DI = {  # F1.com CDN driver portraits
    "George Russell":    "https://www.formula1.com/content/dam/fom-website/drivers/G/GEORUS01_George_Russell/georus01.png.transform/2col/image.png",
    "Kimi Antonelli":    "https://www.formula1.com/content/dam/fom-website/drivers/A/ANDANT01_Kimi_Antonelli/andant01.png.transform/2col/image.png",
    "Charles Leclerc":   "https://www.formula1.com/content/dam/fom-website/drivers/C/CHALEC01_Charles_Leclerc/chalec01.png.transform/2col/image.png",
    "Lewis Hamilton":    "https://www.formula1.com/content/dam/fom-website/drivers/L/LEWHAM01_Lewis_Hamilton/lewham01.png.transform/2col/image.png",
    "Lando Norris":      "https://www.formula1.com/content/dam/fom-website/drivers/L/LANNOR01_Lando_Norris/lannor01.png.transform/2col/image.png",
    "Oscar Piastri":     "https://www.formula1.com/content/dam/fom-website/drivers/O/OSCPIA01_Oscar_Piastri/oscpia01.png.transform/2col/image.png",
    "Max Verstappen":    "https://www.formula1.com/content/dam/fom-website/drivers/M/MAXVER01_Max_Verstappen/maxver01.png.transform/2col/image.png",
    "Isack Hadjar":      "https://www.formula1.com/content/dam/fom-website/drivers/I/ISAHAD01_Isack_Hadjar/isahad01.png.transform/2col/image.png",
    "Fernando Alonso":   "https://www.formula1.com/content/dam/fom-website/drivers/F/FERALO01_Fernando_Alonso/feralo01.png.transform/2col/image.png",
    "Lance Stroll":      "https://www.formula1.com/content/dam/fom-website/drivers/L/LANSTR01_Lance_Stroll/lanstr01.png.transform/2col/image.png",
    "Pierre Gasly":      "https://www.formula1.com/content/dam/fom-website/drivers/P/PIEGAS01_Pierre_Gasly/piegas01.png.transform/2col/image.png",
    "Franco Colapinto":  "https://www.formula1.com/content/dam/fom-website/drivers/F/FRACOL01_Franco_Colapinto/fracol01.png.transform/2col/image.png",
    "Nico Hulkenberg":   "https://www.formula1.com/content/dam/fom-website/drivers/N/NICHUL01_Nico_Hulkenberg/nichul01.png.transform/2col/image.png",
    "Gabriel Bortoleto": "https://www.formula1.com/content/dam/fom-website/drivers/G/GABBOR01_Gabriel_Bortoleto/gabbor01.png.transform/2col/image.png",
    "Liam Lawson":       "https://www.formula1.com/content/dam/fom-website/drivers/L/LIALAW01_Liam_Lawson/lialaw01.png.transform/2col/image.png",
    "Arvid Lindblad":    "https://www.formula1.com/content/dam/fom-website/drivers/A/ARVLIN01_Arvid_Lindblad/arvlin01.png.transform/2col/image.png",
    "Oliver Bearman":    "https://www.formula1.com/content/dam/fom-website/drivers/O/OLIBEA01_Oliver_Bearman/olibea01.png.transform/2col/image.png",
    "Esteban Ocon":      "https://www.formula1.com/content/dam/fom-website/drivers/E/ESTOCO01_Esteban_Ocon/estoco01.png.transform/2col/image.png",
    "Carlos Sainz":      "https://www.formula1.com/content/dam/fom-website/drivers/C/CARSAI01_Carlos_Sainz/carsai01.png.transform/2col/image.png",
    "Alexander Albon":   "https://www.formula1.com/content/dam/fom-website/drivers/A/ALEALB01_Alexander_Albon/alealb01.png.transform/2col/image.png",
    "Sergio Perez":      "https://www.formula1.com/content/dam/fom-website/drivers/S/SERPER01_Sergio_Perez/serper01.png.transform/2col/image.png",
    "Valtteri Bottas":   "https://www.formula1.com/content/dam/fom-website/drivers/V/VALBOT01_Valtteri_Bottas/valbot01.png.transform/2col/image.png",
}
DW = {d: v.get("image_url","") for d,v in DRIVER_DATA.items()} if DRIVER_DATA else {}

# ─── Circuit data ─────────────────────────────────────────────────────────────

CI = {
    "Australian Grand Prix":    {"flag":"🇦🇺","turns":16,"length":"5.303","type":"Street",   "opened":1996,"laps":58,"dist":307},
    "Chinese Grand Prix":       {"flag":"🇨🇳","turns":16,"length":"5.451","type":"Permanent","opened":2004,"laps":56,"dist":305},
    "Japanese Grand Prix":      {"flag":"🇯🇵","turns":18,"length":"5.807","type":"Permanent","opened":1987,"laps":53,"dist":307},
    "Bahrain Grand Prix":       {"flag":"🇧🇭","turns":15,"length":"5.412","type":"Permanent","opened":2004,"laps":57,"dist":308},
    "Saudi Arabian Grand Prix": {"flag":"🇸🇦","turns":27,"length":"6.174","type":"Street",   "opened":2021,"laps":50,"dist":308},
    "Miami Grand Prix":         {"flag":"🇺🇸","turns":19,"length":"5.412","type":"Street",   "opened":2022,"laps":57,"dist":308},
    "Emilia Romagna Grand Prix":{"flag":"🇮🇹","turns":19,"length":"4.909","type":"Permanent","opened":1980,"laps":63,"dist":309},
    "Monaco Grand Prix":        {"flag":"🇲🇨","turns":19,"length":"3.337","type":"Street",   "opened":1929,"laps":78,"dist":260},
    "Spanish Grand Prix":       {"flag":"🇪🇸","turns":14,"length":"4.675","type":"Permanent","opened":1991,"laps":66,"dist":308},
    "Canadian Grand Prix":      {"flag":"🇨🇦","turns":14,"length":"4.361","type":"Street",   "opened":1978,"laps":70,"dist":305},
    "Austrian Grand Prix":      {"flag":"🇦🇹","turns":10,"length":"4.318","type":"Permanent","opened":1970,"laps":71,"dist":307},
    "British Grand Prix":       {"flag":"🇬🇧","turns":18,"length":"5.891","type":"Permanent","opened":1950,"laps":52,"dist":306},
    "Belgian Grand Prix":       {"flag":"🇧🇪","turns":19,"length":"7.004","type":"Permanent","opened":1950,"laps":44,"dist":308},
    "Hungarian Grand Prix":     {"flag":"🇭🇺","turns":14,"length":"4.381","type":"Permanent","opened":1986,"laps":70,"dist":307},
    "Dutch Grand Prix":         {"flag":"🇳🇱","turns":14,"length":"4.259","type":"Permanent","opened":1952,"laps":72,"dist":306},
    "Italian Grand Prix":       {"flag":"🇮🇹","turns":11,"length":"5.793","type":"Permanent","opened":1922,"laps":53,"dist":307},
    "Azerbaijan Grand Prix":    {"flag":"🇦🇿","turns":20,"length":"6.003","type":"Street",   "opened":2016,"laps":51,"dist":306},
    "Singapore Grand Prix":     {"flag":"🇸🇬","turns":19,"length":"4.940","type":"Street",   "opened":2008,"laps":62,"dist":306},
    "United States Grand Prix": {"flag":"🇺🇸","turns":20,"length":"5.513","type":"Permanent","opened":2012,"laps":56,"dist":308},
    "Mexico City Grand Prix":   {"flag":"🇲🇽","turns":17,"length":"4.304","type":"Permanent","opened":1963,"laps":71,"dist":305},
    "São Paulo Grand Prix":     {"flag":"🇧🇷","turns":15,"length":"4.309","type":"Permanent","opened":1973,"laps":71,"dist":305},
    "Las Vegas Grand Prix":     {"flag":"🇺🇸","turns":17,"length":"6.120","type":"Street",   "opened":2023,"laps":50,"dist":306},
    "Qatar Grand Prix":         {"flag":"🇶🇦","turns":16,"length":"5.380","type":"Permanent","opened":2004,"laps":57,"dist":306},
    "Abu Dhabi Grand Prix":     {"flag":"🇦🇪","turns":16,"length":"5.281","type":"Permanent","opened":2009,"laps":58,"dist":306},
}

# Race-specific insights
INS = {
    "Australian Grand Prix":    {"ov":5,"sc":35,"td":5,"spd":232,"drs":3,"corner":"Turn 1","char":"Mixed"},
    "Chinese Grand Prix":       {"ov":7,"sc":20,"td":7,"spd":210,"drs":2,"corner":"Turn 1","char":"High-Speed"},
    "Japanese Grand Prix":      {"ov":4,"sc":30,"td":6,"spd":228,"drs":2,"corner":"130R","char":"Technical"},
    "Bahrain Grand Prix":       {"ov":8,"sc":15,"td":8,"spd":198,"drs":3,"corner":"Turn 4","char":"Mixed"},
    "Saudi Arabian Grand Prix": {"ov":7,"sc":55,"td":3,"spd":252,"drs":3,"corner":"Turn 27","char":"High-Speed"},
    "Miami Grand Prix":         {"ov":6,"sc":35,"td":5,"spd":215,"drs":3,"corner":"Turn 17","char":"Street"},
    "Emilia Romagna Grand Prix":{"ov":4,"sc":25,"td":5,"spd":233,"drs":2,"corner":"Variante Alta","char":"Technical"},
    "Monaco Grand Prix":        {"ov":1,"sc":85,"td":2,"spd":157,"drs":1,"corner":"Rascasse","char":"Street"},
    "Spanish Grand Prix":       {"ov":5,"sc":15,"td":7,"spd":213,"drs":2,"corner":"Turn 1","char":"Technical"},
    "Canadian Grand Prix":      {"ov":7,"sc":45,"td":4,"spd":214,"drs":2,"corner":"Hairpin","char":"Mixed"},
    "Austrian Grand Prix":      {"ov":7,"sc":20,"td":6,"spd":234,"drs":3,"corner":"Turn 3","char":"High-Speed"},
    "British Grand Prix":       {"ov":6,"sc":20,"td":6,"spd":235,"drs":2,"corner":"Copse","char":"High-Speed"},
    "Belgian Grand Prix":       {"ov":8,"sc":30,"td":5,"spd":237,"drs":2,"corner":"Eau Rouge","char":"High-Speed"},
    "Hungarian Grand Prix":     {"ov":3,"sc":15,"td":7,"spd":196,"drs":1,"corner":"Turn 1","char":"Technical"},
    "Dutch Grand Prix":         {"ov":3,"sc":25,"td":6,"spd":214,"drs":1,"corner":"Hugenholtz","char":"Technical"},
    "Italian Grand Prix":       {"ov":9,"sc":20,"td":3,"spd":263,"drs":2,"corner":"Lesmo 1","char":"High-Speed"},
    "Azerbaijan Grand Prix":    {"ov":8,"sc":55,"td":3,"spd":215,"drs":2,"corner":"Turn 8","char":"Street"},
    "Singapore Grand Prix":     {"ov":3,"sc":70,"td":4,"spd":163,"drs":3,"corner":"Turn 10","char":"Street"},
    "United States Grand Prix": {"ov":6,"sc":20,"td":7,"spd":198,"drs":2,"corner":"Turn 1","char":"Mixed"},
    "Mexico City Grand Prix":   {"ov":7,"sc":20,"td":6,"spd":213,"drs":3,"corner":"Esses","char":"Mixed"},
    "São Paulo Grand Prix":     {"ov":7,"sc":35,"td":5,"spd":215,"drs":2,"corner":"Senna S","char":"Mixed"},
    "Las Vegas Grand Prix":     {"ov":7,"sc":40,"td":3,"spd":218,"drs":3,"corner":"Turn 14","char":"Street"},
    "Qatar Grand Prix":         {"ov":4,"sc":30,"td":9,"spd":220,"drs":2,"corner":"Turn 1","char":"High-Speed"},
    "Abu Dhabi Grand Prix":     {"ov":5,"sc":20,"td":5,"spd":210,"drs":2,"corner":"Turn 5","char":"Mixed"},
}
_DINS = {"ov":5,"sc":25,"td":5,"spd":210,"drs":2,"corner":"Turn 1","char":"Mixed"}

# Hero carousel images: 4 per circuit
# Slot 0 = full landscape, Slot 1 = entropy crop, Slot 2 = bottom crop, Slot 3 = top crop
_UNSPLASH = {
    "Australian Grand Prix":    "https://images.unsplash.com/photo-1558618666-fcd25c85cd64",
    "Chinese Grand Prix":       "https://images.unsplash.com/photo-1547471080-7cc2caa01a7e",
    "Japanese Grand Prix":      "https://images.unsplash.com/photo-1528360983277-13d401cdc186",
    "Bahrain Grand Prix":       "https://images.unsplash.com/photo-1466442929976-97f336a657be",
    "Saudi Arabian Grand Prix": "https://images.unsplash.com/photo-1586861256632-a2baa6af0a25",
    "Miami Grand Prix":         "https://images.unsplash.com/photo-1514214246283-d427a95c5d2f",
    "Monaco Grand Prix":        "https://images.unsplash.com/photo-1539037116277-4db20889f2d4",
    "Spanish Grand Prix":       "https://images.unsplash.com/photo-1504019347908-b45f9b0b8dd5",
    "Canadian Grand Prix":      "https://images.unsplash.com/photo-1534430480872-3498386e7856",
    "British Grand Prix":       "https://images.unsplash.com/photo-1500829243541-74b677fecc30",
    "Austrian Grand Prix":      "https://images.unsplash.com/photo-1527576539890-dfa815648363",
    "Belgian Grand Prix":       "https://images.unsplash.com/photo-1476067897447-d28b660ec3a4",
    "Dutch Grand Prix":         "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429",
    "Italian Grand Prix":       "https://images.unsplash.com/photo-1519452635265-7b1fbfd1e4e0",
    "Azerbaijan Grand Prix":    "https://images.unsplash.com/photo-1578662996442-48f60103fc96",
    "Singapore Grand Prix":     "https://images.unsplash.com/photo-1525625293386-3f8f99389edd",
    "United States Grand Prix": "https://images.unsplash.com/photo-1531219432768-9f540ce91ef3",
    "Mexico City Grand Prix":   "https://images.unsplash.com/photo-1518105779142-d975f22f1b0a",
    "São Paulo Grand Prix":     "https://images.unsplash.com/photo-1483729558449-99ef09a8c325",
    "Las Vegas Grand Prix":     "https://images.unsplash.com/photo-1581351721010-8cf859cb14a4",
    "Qatar Grand Prix":         "https://images.unsplash.com/photo-1553689557-c2fc0f7e8d83",
    "Abu Dhabi Grand Prix":     "https://images.unsplash.com/photo-1512453979798-5ea266f8880c",
    "Hungarian Grand Prix":     "https://images.unsplash.com/photo-1534430480872-3498386e7856",
    "Emilia Romagna Grand Prix":"https://images.unsplash.com/photo-1519452635265-7b1fbfd1e4e0",
}
_DEFAULT_U = "https://images.unsplash.com/photo-1558618666-fcd25c85cd64"

_CROPS = [
    "?w=1920&h=900&fit=crop&crop=center&q=88",
    "?w=1920&h=900&fit=crop&crop=entropy&q=88",
    "?w=1920&h=900&fit=crop&crop=bottom&q=88",
    "?w=1920&h=900&fit=crop&crop=top&q=88",
]

def _hero_imgs(circuit: str) -> list:
    base = _UNSPLASH.get(circuit, _DEFAULT_U)
    return [base + c for c in _CROPS]

WEATHER_ICON = {"Dry":"&#9728;","Mixed":"&#9925;","Wet":"&#127783;"}
CHAR_COLOR   = {"Technical":"#6692FF","High-Speed":"#27F4D2","Street":"#FF87BC","Mixed":"#FFD700"}
MEDAL = {
    1:{"c":"#FFD700","g":"linear-gradient(135deg,#FFD700,#FFA500)","s":"#FFD70060"},
    2:{"c":"#C0C0C0","g":"linear-gradient(135deg,#C0C0C0,#888)","s":"#C0C0C060"},
    3:{"c":"#CD7F32","g":"linear-gradient(135deg,#CD7F32,#9A5A1D)","s":"#CD7F3260"},
}
PH = {1:88, 2:58, 3:44}   # plinth heights


# ─── Driver card ──────────────────────────────────────────────────────────────

def _card(row: dict, pos: int, delay: int) -> str:
    name = row.get("driver","?")
    team = row.get("team","")
    wp   = row.get("win_prob",0)*100
    pp   = row.get("podium_prob",0)*100
    qual = row.get("qualifying_position","?")
    tc = TC.get(team,"#888")
    mc = MEDAL[pos]["c"];  mg = MEDAL[pos]["g"];  ms = MEDAL[pos]["s"]
    ph = PH[pos]

    parts = name.split()
    fi  = parts[0][0]+"." if len(parts)>1 else ""
    ln  = parts[-1].upper() if parts else name.upper()
    abr = (parts[0][0]+parts[-1][:2]).upper() if len(parts)>1 else name[:3].upper()
    i1  = DI.get(name,"");  i2  = DW.get(name,"")

    if i1:
        img = (
            '<img src="'+i1+'" style="width:100%;height:100%;object-fit:cover;object-position:top;" '
            'onerror="this.src=\''+i2+'\';this.onerror=function(){'
            'this.parentElement.innerHTML=\'<div style=&quot;display:flex;width:100%;height:100%;'
            'align-items:center;justify-content:center;font-family:Orbitron,monospace;font-size:1rem;'
            'font-weight:900;color:'+tc+';&quot;>'+abr+'</div>\'}" />'
        )
    else:
        img = ('<div style="display:flex;width:100%;height:100%;align-items:center;justify-content:center;'
               'font-family:Orbitron,monospace;font-size:1rem;font-weight:900;color:'+tc+';">'+abr+'</div>')

    wb = min(wp*2.5,100);  pb = min(pp,100)
    # P1 gets a slightly larger card
    photo_sz = "80px" if pos==1 else "68px"
    font_sz  = "0.68rem" if pos==1 else "0.62rem"

    return (
        '<div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-end;'
        'flex:0 0 auto;width:'+ ("192px" if pos==1 else "168px") +';'
        'animation:riseUp 0.9s cubic-bezier(0.16,1,0.3,1) '+str(delay)+'ms both;">'

        # Card body
        '<div style="width:100%;border-radius:14px;overflow:hidden;margin-bottom:4px;position:relative;'
        'background:rgba(6,6,14,0.88);'
        'backdrop-filter:blur(28px);-webkit-backdrop-filter:blur(28px);'
        'border:1px solid '+tc+'2E;'
        'box-shadow:0 4px 28px '+ms+',0 12px 40px rgba(0,0,0,0.7);'
        'transition:transform 0.25s ease,box-shadow 0.25s ease;"'
        ' onmouseenter="this.style.transform=\'translateY(-4px)\';this.style.boxShadow=\'0 10px 40px '+ms+',0 20px 60px rgba(0,0,0,0.8)\'"'
        ' onmouseleave="this.style.transform=\'\';this.style.boxShadow=\'0 4px 28px '+ms+',0 12px 40px rgba(0,0,0,0.7)\'">'

        # Medal stripe + position badge
        '<div style="height:3px;background:'+mg+';width:100%;"></div>'
        '<div style="position:absolute;top:9px;left:11px;font-family:Orbitron,monospace;'
        'font-size:0.52rem;font-weight:900;color:'+mc+';letter-spacing:2px;">P'+str(pos)+'</div>'

        '<div style="padding:12px 11px 11px;">'

        # Photo
        '<div style="width:'+photo_sz+';height:'+photo_sz+';border-radius:50%;'
        'margin:18px auto 10px;overflow:hidden;border:2px solid '+tc+'50;'
        'box-shadow:0 0 20px '+tc+'38;background:#0A0A16;">'+img+'</div>'

        # Name
        '<div style="text-align:center;margin-bottom:7px;">'
        '<div style="font-family:Orbitron,monospace;font-size:'+font_sz+';font-weight:700;'
        'color:#FFF;letter-spacing:0.3px;">'+fi+'&nbsp;'+ln+'</div>'
        '<div style="font-size:0.52rem;color:'+tc+';letter-spacing:1.5px;text-transform:uppercase;margin-top:2px;">'+team+'</div>'
        '</div>'

        # Win bar
        '<div style="margin-bottom:5px;">'
        '<div style="display:flex;justify-content:space-between;margin-bottom:2px;">'
        '<span style="font-size:0.46rem;color:#55556A;letter-spacing:1px;">WIN</span>'
        '<span style="font-family:Orbitron,monospace;font-size:0.52rem;color:'+mc+';">'
        +'{:.1f}'.format(wp)+'%</span></div>'
        '<div style="height:3px;background:#0C0C1A;border-radius:2px;">'
        '<div style="width:'+'{:.0f}'.format(wb)+'%;height:100%;background:'+mg+';border-radius:2px;"></div>'
        '</div></div>'

        # Podium bar
        '<div><div style="display:flex;justify-content:space-between;margin-bottom:2px;">'
        '<span style="font-size:0.46rem;color:#55556A;letter-spacing:1px;">PODIUM</span>'
        '<span style="font-family:Orbitron,monospace;font-size:0.52rem;color:'+tc+';">'
        +'{:.1f}'.format(pp)+'%</span></div>'
        '<div style="height:3px;background:#0C0C1A;border-radius:2px;">'
        '<div style="width:'+'{:.0f}'.format(pb)+'%;height:100%;background:'+tc+'95;border-radius:2px;"></div>'
        '</div></div>'

        # Qual
        '<div style="margin-top:8px;padding-top:6px;border-top:1px solid #14142A;'
        'text-align:center;font-size:0.48rem;color:#44445E;letter-spacing:1px;">'
        'QUAL <span style="color:'+tc+';font-family:Orbitron,monospace;">P'+str(qual)+'</span>'
        '</div>'
        '</div></div>'  # end card body

        # Plinth
        '<div style="width:100%;height:'+str(ph)+'px;'
        'background:linear-gradient(180deg,'+tc+'18,'+tc+'06);'
        'border:1px solid '+tc+'20;border-bottom:none;border-radius:8px 8px 0 0;'
        'display:flex;align-items:center;justify-content:center;">'
        '<div style="font-family:Orbitron,monospace;font-size:'+('2.4rem' if pos==1 else '1.9rem')+';'
        'font-weight:900;color:'+mc+';text-shadow:0 0 24px '+mc+'70;">'+str(pos)+'</div>'
        '</div>'
        '</div>'
    )


# ─── Render ───────────────────────────────────────────────────────────────────

def render_podium(pred: dict, circuit: str, weather: str) -> str:
    top3 = pred.get("top_10",[])[:3]
    if len(top3) < 3:
        return ""

    p1, p2, p3 = top3[0], top3[1], top3[2]

    ci   = CI.get(circuit, {"flag":"🏁","turns":15,"length":"5.0","type":"Mixed","opened":2000,"laps":55,"dist":305})
    ins  = INS.get(circuit, _DINS)
    imgs = _hero_imgs(circuit)

    flag   = ci["flag"];   turns  = ci["turns"]
    length = ci["length"]; ctype  = ci["type"]
    year   = ci["opened"]; laps   = ci["laps"];  dist = ci["dist"]
    short  = circuit.replace(" Grand Prix","").upper()
    wicon  = WEATHER_ICON.get(weather,"&#9925;")
    chc    = CHAR_COLOR.get(ins["char"],"#FFD700")

    c1 = _card(p1,1,120);  c2 = _card(p2,2,260);  c3 = _card(p3,3,400)

    # ── Insight mini-pills ─────────────────────────────────────────────────────
    def pill(label, val, color="#E8002D"):
        return (
            '<div style="display:flex;flex-direction:column;align-items:center;gap:3px;'
            'background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);'
            'border-radius:10px;padding:9px 14px;min-width:72px;">'
            '<div style="font-family:Orbitron,monospace;font-size:0.82rem;font-weight:700;color:'+color+';">'+str(val)+'</div>'
            '<div style="font-size:0.44rem;color:#555570;letter-spacing:1.2px;text-transform:uppercase;">'+label+'</div>'
            '</div>'
        )

    sc_c  = "#E8002D" if ins["sc"]>60 else "#FFD700" if ins["sc"]>35 else "#27F4D2"
    ov_c  = "#27F4D2" if ins["ov"]>6 else "#FFD700" if ins["ov"]>3 else "#E8002D"
    td_c  = "#E8002D" if ins["td"]>7 else "#FFD700" if ins["td"]>4 else "#27F4D2"

    # Pre-build pills so we avoid multi-line concatenation inside the return string
    pills_html = (
        pill("LAPS",      laps,                  "#E8002D") +
        pill("KM/LAP",    length,                "#E8002D") +
        pill("TURNS",     turns,                 "#E8002D") +
        pill("TOTAL KM",  dist,                  "#E8002D") +
        pill("SC RISK",   str(ins["sc"])+"%",    sc_c)      +
        pill("OVERTAKE",  str(ins["ov"])+"/10",  ov_c)      +
        pill("TYRE DEG",  str(ins["td"])+"/10",  td_c)      +
        pill("DRS ZONES", ins["drs"],             chc)
    )

    # ── Thumbnail strip ────────────────────────────────────────────────────────
    thumbs_html = ""
    for i,url in enumerate(imgs):
        active_style = "border:2px solid #E8002D;opacity:1;" if i==0 else "border:2px solid rgba(255,255,255,0.18);opacity:0.65;"
        thumbs_html += (
            '<div onclick="heroGo('+str(i)+')" '
            'style="width:72px;height:46px;border-radius:7px;overflow:hidden;cursor:pointer;'
            'flex-shrink:0;transition:all 0.3s ease;'+active_style+'" '
            'id="thumb-'+str(i)+'">'
            '<img src="'+url+'" style="width:100%;height:100%;object-fit:cover;" '
            'loading="lazy" onerror="this.parentElement.style.display=\'none\'" />'
            '</div>'
        )

    # ── Carousel JS ───────────────────────────────────────────────────────────
    bg_vars = "var _bgs=['" + "','".join(imgs) + "'];"
    n       = len(imgs)
    dot_html = "".join(
        '<div class="hdot" data-i="'+str(i)+'" '
        'style="width:7px;height:7px;border-radius:50%;cursor:pointer;transition:all 0.3s;'
        'background:'+('"#E8002D"' if i==0 else '"rgba(255,255,255,0.3)"')+';'
        'transform:'+('"scale(1.3)"' if i==0 else '"scale(1)"')+'"></div>'
        for i in range(n)
    )

    js = (
        '<script>'
        + bg_vars
        + 'var _hi=0,_hn='+str(n)+';'
        + 'var _bg=document.getElementById("hero-bg");'
        + 'var _dots=document.querySelectorAll(".hdot");'
        + 'var _thumbEls=document.querySelectorAll("[id^=thumb-]");'
        + 'function heroGo(idx){'
        +   '_hi=idx;'
        +   '_bg.style.backgroundImage="url("+_bgs[_hi]+")";'
        +   '_dots.forEach(function(d,i){'
        +     'd.style.background=i===_hi?"#E8002D":"rgba(255,255,255,0.3)";'
        +     'd.style.transform=i===_hi?"scale(1.3)":"scale(1)";'
        +   '});'
        +   '_thumbEls.forEach(function(t,i){'
        +     't.style.border=i===_hi?"2px solid #E8002D":"2px solid rgba(255,255,255,0.18)";'
        +     't.style.opacity=i===_hi?"1":"0.65";'
        +   '});'
        + '}'
        + 'function heroNext(){heroGo((_hi+1)%_hn);}'
        + 'function heroPrev(){heroGo((_hi-1+_hn)%_hn);}'
        + 'var _ht=setInterval(heroNext,5000);'
        + 'document.getElementById("hero-bg").addEventListener("mouseenter",function(){clearInterval(_ht);});'
        + '</script>'
    )

    return """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html,body{width:100%;height:960px;background:#030306;overflow:hidden;font-family:'Inter',sans-serif}

/* Hero background */
#hero-bg{
  position:absolute;inset:0;
  background-image:url('""" + imgs[0] + """');
  background-size:cover;background-position:center;
  transition:background-image 0.01s, opacity 0.8s ease;
  animation:heroReveal 1.8s cubic-bezier(0.16,1,0.3,1) both;
  will-change:transform;
}

/* Gradient layers */
#grad-top{position:absolute;inset:0;background:linear-gradient(180deg,rgba(3,3,6,0.68) 0%,rgba(3,3,6,0.0) 35%,rgba(3,3,6,0.0) 50%,rgba(3,3,6,0.72) 68%,rgba(3,3,6,0.97) 100%);}
#grad-vignette{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 0%,transparent 40%,rgba(3,3,6,0.45) 100%);}

@keyframes heroReveal{0%{opacity:0;transform:scale(1.08)}100%{opacity:1;transform:scale(1)}}
@keyframes riseUp{0%{opacity:0;transform:translateY(44px)}100%{opacity:1;transform:translateY(0)}}
@keyframes fadeSlide{0%{opacity:0;transform:translateY(-14px)}100%{opacity:1;transform:translateY(0)}}
@keyframes fadeIn{0%{opacity:0}100%{opacity:1}}
@keyframes pulse{0%,100%{box-shadow:0 0 5px #E8002D80}50%{box-shadow:0 0 14px #E8002D}}
@keyframes scanH{0%{left:-40%}100%{left:140%}}

/* Arrow buttons */
.hero-arrow{
  position:absolute;top:50%;transform:translateY(-50%);
  background:rgba(6,6,12,0.70);border:1px solid rgba(232,0,45,0.55);
  color:#fff;border-radius:50%;width:40px;height:40px;cursor:pointer;
  font-size:1.3rem;display:flex;align-items:center;justify-content:center;
  z-index:20;transition:all 0.2s ease;padding:0;
  backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
}
.hero-arrow:hover{background:#E8002D;border-color:#E8002D;transform:translateY(-50%) scale(1.1);}
button:focus{outline:none}
</style></head><body>

<div id="root" style="position:relative;width:100%;height:960px;overflow:hidden;background:#030306;">

  <!-- ░░ HERO BACKGROUND ░░ -->
  <div id="hero-bg"></div>
  <div id="grad-top"></div>
  <div id="grad-vignette"></div>

  <!-- Scan highlight line -->
  <div style="position:absolute;top:0;bottom:0;width:2px;pointer-events:none;z-index:1;
    background:linear-gradient(180deg,transparent,rgba(232,0,45,0.4),transparent);
    animation:scanH 7s ease-in-out infinite;"></div>

  <!-- ░░ TOP BAR ░░ -->
  <div style="position:absolute;top:0;left:0;right:0;padding:18px 28px;
    display:flex;justify-content:space-between;align-items:flex-start;z-index:30;
    animation:fadeSlide 1s cubic-bezier(0.16,1,0.3,1) 0.1s both;">

    <!-- Live badge -->
    <div style="display:flex;align-items:center;gap:9px;
      background:rgba(232,0,45,0.10);border:1px solid rgba(232,0,45,0.50);
      border-radius:9px;padding:8px 16px;
      backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);">
      <div style="width:7px;height:7px;border-radius:50%;background:#E8002D;animation:pulse 1.6s ease infinite;flex-shrink:0;"></div>
      <span style="font-family:'Orbitron',monospace;font-size:0.56rem;font-weight:700;
        color:#E8002D;letter-spacing:2.5px;white-space:nowrap;">PITWALL AI &middot; 2026</span>
    </div>

    <!-- Circuit identity -->
    <div style="flex:1;text-align:center;padding:0 16px;">
      <div style="font-size:1.7rem;margin-bottom:2px;line-height:1;">""" + flag + """</div>
      <div style="font-family:'Orbitron',monospace;font-size:1.18rem;font-weight:900;
        color:#FFFFFF;letter-spacing:-0.3px;
        text-shadow:0 2px 32px rgba(0,0,0,0.95),0 0 60px rgba(232,0,45,0.12);">""" + short + """</div>
      <div style="margin-top:4px;display:flex;align-items:center;justify-content:center;gap:8px;">
        <span style="font-size:0.52rem;color:#888898;letter-spacing:2px;text-transform:uppercase;">""" + ctype + """ &middot; EST. """ + str(year) + """</span>
        <span style="display:inline-block;background:""" + chc + """18;border:1px solid """ + chc + """55;
          border-radius:4px;padding:2px 7px;font-family:'Orbitron',monospace;
          font-size:0.46rem;color:""" + chc + """;letter-spacing:1px;">""" + ins["char"].upper() + """</span>
      </div>
    </div>

    <!-- Weather -->
    <div style="display:flex;align-items:center;gap:9px;
      background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.13);
      border-radius:9px;padding:8px 14px;
      backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);">
      <span style="font-size:1.4rem;">""" + wicon + """</span>
      <div>
        <div style="font-family:'Orbitron',monospace;font-size:0.56rem;color:#FFF;letter-spacing:1.5px;">""" + weather.upper() + """</div>
        <div style="font-size:0.46rem;color:#666680;margin-top:1px;letter-spacing:1px;">CONDITIONS</div>
      </div>
    </div>
  </div>

  <!-- ░░ CAROUSEL ARROWS (mid-hero) ░░ -->
  <button class="hero-arrow" style="left:16px;" onclick="heroPrev()">&#8249;</button>
  <button class="hero-arrow" style="right:16px;" onclick="heroNext()">&#8250;</button>

  <!-- ░░ CAROUSEL DOTS (above thumbnail strip) ░░ -->
  <div style="position:absolute;bottom:432px;left:50%;transform:translateX(-50%);
    display:flex;gap:6px;z-index:25;animation:fadeIn 0.8s ease 0.4s both;">
    """ + dot_html + """
  </div>

  <!-- ░░ THUMBNAIL STRIP ░░ -->
  <div style="position:absolute;bottom:376px;left:50%;transform:translateX(-50%);
    display:flex;gap:8px;z-index:25;animation:fadeIn 0.9s ease 0.5s both;">
    """ + thumbs_html + """
  </div>

  <!-- ░░ BOTTOM PREDICTION PANEL ░░ -->
  <div style="position:absolute;bottom:0;left:0;right:0;height:370px;
    background:linear-gradient(180deg,rgba(3,3,6,0.0) 0%,rgba(3,3,6,0.96) 12%,rgba(3,3,6,0.99) 100%);
    backdrop-filter:blur(2px);-webkit-backdrop-filter:blur(2px);">

    <!-- Section label -->
    <div style="text-align:center;padding:0 0 8px;
      animation:fadeIn 0.8s ease 0.2s both;">
      <span style="font-family:'Orbitron',monospace;font-size:0.52rem;font-weight:700;
        color:#E8002D;letter-spacing:4px;text-transform:uppercase;">&#11044;&nbsp; ML PREDICTION &nbsp;&#11044;</span>
    </div>

    <!-- Podium: P2 | P1 | P3 -->
    <div style="display:flex;justify-content:center;align-items:flex-end;
      gap:10px;padding:0 24px;">
      """ + c2 + c1 + c3 + """
    </div>

    <!-- Race metrics bar -->
    <div style="margin-top:8px;
      border-top:1px solid rgba(232,0,45,0.16);
      padding:10px 24px;
      display:flex;justify-content:space-between;align-items:center;
      gap:6px;flex-wrap:nowrap;">

      <!-- F1 brand -->
      <div style="display:flex;align-items:center;gap:10px;flex-shrink:0;">
        <div style="width:3px;height:28px;background:linear-gradient(#E8002D,#FF6B35);border-radius:2px;"></div>
        <div>
          <div style="font-family:'Orbitron',monospace;font-size:0.75rem;font-weight:900;color:#FFF;">FORMULA 1</div>
          <div style="font-size:0.46rem;color:#E8002D;letter-spacing:2px;text-transform:uppercase;margin-top:1px;">""" + short + """ GP</div>
        </div>
      </div>

      <!-- Stats pills grid -->
      <div style="display:flex;gap:5px;align-items:center;flex:1;justify-content:center;flex-wrap:nowrap;overflow:hidden;">
        """ + pills_html + """
      </div>

      <!-- Key corner badge -->
      <div style="flex-shrink:0;text-align:right;">
        <div style="font-family:'Orbitron',monospace;font-size:0.6rem;font-weight:700;color:#FFF;white-space:nowrap;">""" + ins["corner"] + """</div>
        <div style="font-size:0.44rem;color:#44445E;letter-spacing:1.2px;margin-top:2px;">KEY CORNER</div>
      </div>
    </div>

  </div><!-- /bottom panel -->

""" + js + """

</div><!-- /root -->
</body></html>"""
