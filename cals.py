import React
import {useMemo
        import useState
        import useEffect} from "react"
import {motion} from "framer-motion"
import {
    Calculator,
    PiggyBank,
    Wallet,
    Activity,
    Ruler,
    Percent,
    Sun,
    Moon,
    Link as LinkIcon,
    Save,
    Trash2,
    History,
    Home,
    Sparkles
} from "lucide-react"
import {ResponsiveContainer
        import AreaChart
        import Area
        import XAxis
        import YAxis
        import Tooltip
        import CartesianGrid} from "recharts"


// == == == == == == == == == == = Helpers & Infrastructure == == == == == == == == == == = //

async function callGemini(prompt, retries=3, delay=1000) {
    const apiKey = ""
    // API key will be injected by the environment
    const apiUrl = `https: // generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20: generateContent?key =${apiKey}`

    const payload = {
        contents: [{parts: [{text: prompt}]}],
    }

    for (let i=0
         i < retries
         i++) {
        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            })

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }

            const result = await response.json()

            if (result.candidates & & result.candidates.length > 0 & & result.candidates[0].content?.parts?.[0]?.text) {
                return result.candidates[0].content.parts[0].text
            } else {
                throw new Error("API response did not contain valid text.")
            }

        } catch(error) {
            console.error(`Attempt ${i + 1} failed: `, error)
            if (i === retries - 1) {
                throw error
            }
            await new Promise(res=> setTimeout(res, delay * Math.pow(2, i)))
        }
    }
    throw new Error("All API call attempts failed.")
}


// Minimal Jalaali(Shamsi) & Hijri conversion utilities
function div(a, b){return Math.floor(a / b)
                   }

function toJalaali(gy, gm, gd){
    const g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    let jy = (gy <= 1600)?0: 979
    gy -= (gy <= 1600)?621: 1600
    let gy2 = (gm > 2)?(gy+1): gy
    let days = 365*gy + div((gy2+3), 4) - div((gy2+99), 100) + div((gy2+399), 400) - 80 + gd + g_d_m[gm-1]
    jy += 33*div(days, 12053)
    days %= 12053
    jy += 4*div(days, 1461)
    days %= 1461
    if (days > 365){
        jy += div((days-1), 365)
        days = (days-1) % 365
    }
    const jm = (days < 186)? 1+div(days, 31): 7+div(days-186, 30)
    const jd = 1 + ((days < 186)? (days % 31): ((days-186) % 30))
    return {jy, jm, jd}
}

function toGregorian(jy, jm, jd){
    const gy = (jy <= 979)?621: 1600
    jy -= (jy <= 979)?0: 979
    let days = 365*jy + div(jy, 33)*8 + div((jy % 33)+3, 4) + 78 + jd + ((jm < 7)? (jm-1)*31: ((jm-7)*30+186))
    let gy2 = gy + 400*div(days, 146097)
    days %= 146097
    let leap = true
    if (days >= 36525){
        days--
        gy2 += 100*div(days, 36524)
        days %= 36524
        if (days >= 365) days++
        else leap = false
    }
    gy2 += 4*div(days, 1461)
    days %= 1461
    if (days >= 366){
        leap = false
        days--
        gy2 += div(days, 365)
        days %= 365
    }
    const sal_a = [0, 31, (leap?29: 28), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    let gm = 0, gd = 0
    for (gm=1
         gm <= 12 & & days >= sal_a[gm]
         gm++) days -= sal_a[gm]
    gd = days+1
    return {gy: gy2, gm, gd}
}

function gregorianToHijri(gy, gm, gd) {
    const jd = gregorianToJD(gy, gm, gd)
    return jdToIslamic(jd)
}

function hijriToGregorian(hy, hm, hd){
    const jd = islamicToJD(hy, hm, hd)
    return jdToGregorian(jd)
}

function gregorianToJD(y, m, d){
    if (m <= 2){y -= 1
                m += 12
                }
    const A = Math.floor(y/100)
    const B = 2 - A + Math.floor(A/4)
    return Math.floor(365.25*(y+4716)) + Math.floor(30.6001*(m+1)) + d + B - 1524.5
}

function jdToGregorian(jd){
    jd = jd + 0.5
    const Z = Math.floor(jd), F = jd - Z
    let A = Z
    const alpha = Math.floor((Z - 1867216.25)/36524.25)
    A = Z + 1 + alpha - Math.floor(alpha/4)
    const B = A + 1524
    const C = Math.floor((B - 122.1)/365.25)
    const D = Math.floor(365.25*C)
    const E = Math.floor((B - D)/30.6001)
    const day = B - D - Math.floor(30.6001*E) + F
    const month = (E < 14)?E-1: E-13
    const year = (month > 2)?C-4716: C-4715
    return {gy: year, gm: month, gd: Math.floor(day)}
}

function islamicToJD(y, m, d){
    return Math.floor((11*y + 3)/30) + 354*y + 30*m - Math.floor((m-1)/2) + d + 1948440 - 385 - 0.5
}

function jdToIslamic(jd){
    jd = Math.floor(jd) + 0.5
    const y = Math.floor((30*(jd - 1948439.5) + 10646) / 10631)
    const m = Math.min(12, Math.ceil((jd - (29 + islamicToJD(y, 1, 1))) / 29.5) + 1)
    const d = Math.floor(jd - islamicToJD(y, m, 1)) + 1
    return {hy: y, hm: m, hd: d}
}

const formatNumber = (n) = >
new Intl.NumberFormat("fa-IR", {maximumFractionDigits: 2}).format(
    isNaN(n) ? 0: n
)
const formatCurrency = (n) = > `${formatNumber(n)} تومان`

const ROUTES = [
    {key: "home", label: "همه ابزارها", icon: Home},
    {key: "loan", label: "قسط و وام", icon: PiggyBank},
    {key: "salary", label: "حقوق و اضافه‌کاری", icon: Wallet},
    {key: "bmi", label: "BMI", icon: Activity},
    {key: "vat", label: "مالیات ارزش افزوده", icon: Percent},
    {key: "convert", label: "تبدیل واحد", icon: Ruler},
    {key: "date", label: "تبدیل تاریخ", icon: Ruler},
    {key: "age", label: "سن", icon: Activity},
    {key: "discount", label: "تخفیف", icon: Percent},
    {key: "currency", label: "نرخ ارز", icon: Wallet},
    {key: "bill", label: "تقسیم صورتحساب", icon: Wallet},
    {key: "bmr", label: "BMR/کالری", icon: Activity},
]

function useHashRoute() {
    const parse = () = > {
        const raw = window.location.hash | | ""
        let hash = raw
        if (hash.startsWith("#/")) hash = hash.slice(2)
        else if (hash.startsWith("#")) hash = hash.slice(1)
        const[path, queryString] = hash.split("?")
        const route = ROUTES.find((r)=> r.key == = (path | | "home"))?.key | | "home"
        const params = Object.fromEntries(new URLSearchParams(queryString | | ""))
        return {route, params}
    }
    const [{route, params}, setState] = useState(()= > ({route: "home", params: {}}))
    useEffect(()=> {
        const update = () = > setState(parse())
        update()
        window.addEventListener("hashchange", update)
        return ()= > window.removeEventListener("hashchange", update)
    }, [])
    const navigate = (key, nextParams) = > {
        const qs = nextParams ? `?${new URLSearchParams(nextParams).toString()}`: ""
        window.location.hash = `/${key}${qs}`
    }
    return {route, params, navigate}
}

const HISTORY_KEY = "calc_history_v1"
function pushHistory(entry) {
    try {
        const list = JSON.parse(localStorage.getItem(HISTORY_KEY) | | "[]")
        list.unshift({...entry, ts: Date.now()})
        localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, 100)))
    } catch {}
}
function readHistory() {
    try {
        return JSON.parse(localStorage.getItem(HISTORY_KEY) | | "[]")
    } catch {
        return []
    }
}
function clearHistory() {
    localStorage.removeItem(HISTORY_KEY)
}

function useTheme() {
    const[theme, setTheme] = useState(
        typeof window != = "undefined" & & window.matchMedia & & window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark": "light"
    )
    useEffect(()=> {
        const root= document.documentElement
        if (theme == = "dark") root.classList.add("dark")
        else root.classList.remove("dark")
    }, [theme])
    return {theme, setTheme}
}


// == == == == == == == == == == = UI Components == == == == == == == == == == = //

function Card({className = "", ...props}){return < div className = {`rounded-2xl ${className}`} {...props} / >}
function CardHeader({className= "", ...props}){return < div className = {`p-4 border-b border-neutral-200/60 dark: border-neutral-800/60 ${className}`} {...props} / >}
function CardTitle({className = "", ...props}){return < div className = {`font-bold ${className}`} {...props} / >}
function CardContent({className = "", ...props}){return < div className = {`p-4 ${className}`} {...props} / >}

function Button({className = "", variant = "default", size = "md", ...props}){
    const base = "inline-flex items-center justify-center gap-1 px-3 py-2 text-sm font-medium rounded-xl transition"
    const variantCls = variant == ="secondary" ? "bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 border border-neutral-200 dark:border-neutral-700": variant == ="outline" ? "border border-neutral-300 dark:border-neutral-700 bg-transparent hover:bg-neutral-100 dark:hover:bg-neutral-800": variant == ="ghost" ? "bg-transparent hover:bg-neutral-100 dark:hover:bg-neutral-800": "bg-neutral-900 text-white dark:bg-white dark:text-neutral-900"
    const sizeCls = size == = "sm" ? "px-2 py-1.5 text-xs": ""
    return < button className = {`${base} ${variantCls} ${sizeCls} ${className}`} {...props} / >
}

function Input({className = "", ...props}){
    return < input className = {`w-full mt-1 rounded-md border border-neutral-300 dark: border-neutral-700 bg-white/80 dark: bg-neutral-800/60 px-3 py-2 ${className}`} {...props} / >
}

function Label({className = "", ...props}){
    return < label className = {`text-xs text-neutral-600 dark: text-neutral-300 ${className}`} {...props} / >
}

function Tabs({value, onValueChange, children, className = ""}){
    const ctx = {value, onValueChange}
    return < div className = {className} > {React.Children.map(children, c=> React.cloneElement(c, {ctx}))} < /div >
}
function TabsList({children, className = ""}){return < div className = {`grid gap-2 my-2 ${className}`} > {children} < /div >}
function TabsTrigger({value, children, ctx}){
    const active = ctx?.value == = value
    return < button onClick = {() = >ctx?.onValueChange(value)} className = {`px-3 py-2 rounded-xl text-sm ${active?'bg-neutral-900 text-white dark:bg-white dark:text-neutral-900': 'bg-neutral-100 dark:bg-neutral-800'}`} > {children} < /button >
}
function TabsContent({value, children, ctx}){return ctx?.value == =value ? < div className = "mt-3" > {children} < /div >: null }

function Stat({title, value}) {
    return (
        < div className="p-4 rounded-xl bg-gradient-to-br from-white to-neutral-50 dark:from-neutral-800 dark:to-neutral-900 border border-neutral-200/50 dark:border-neutral-800/60 shadow-inner" >
        < div className="text-xs text-neutral-500 mb-1" > {title} < /div >
        < div className="text-base font-bold" > {value} < /div >
        < / div >
    )
}

// == == == == == == == == == == = Layout Components == == == == == == == == == == = //

function HeaderBar({onToggleTheme, theme, current, onNav}) {
    return (
        < div className="flex flex-col gap-4 mb-6" >
        < div className="flex items-center justify-between gap-4" >
        < div className="flex items-center gap-3" >
        < div className="rounded-xl shadow-lg h-12 w-12 overflow-hidden" >
        < img src="/logo.png" alt="لوگو" className="w-full h-full object-cover" / >
        < /div >
        < div >
        < h1 className="text-xl sm:text-2xl font-extrabold tracking-tight" > ماشین‌حساب‌های کاربردی < /h1 >
        < p className="text-neutral-500 text-sm" > سریع، دقیق و زیبا — برای استفاده روزمره < /p >
        < / div >
        < / div >
        < Button variant="outline" onClick={onToggleTheme} className="rounded-xl" >
        {theme == = "dark" ? (
            < div className="flex items-center gap-2" > <Sun className="w-4 h-4" / > حالت روشن < /div >
        ): (
            < div className="flex items-center gap-2" > <Moon className="w-4 h-4" / > حالت تیره < /div >
        )}
        < /Button >
        < / div >

        < div className="flex flex-wrap gap-2" >
        {ROUTES.map((r)= > (
            < Button
            key={r.key}
            variant={current == = r.key ? "default": "secondary"}
            className={`rounded-xl ${current == = r.key ? "": "bg-white/60 dark:bg-neutral-800/60"}`}
            onClick={()= > onNav(r.key)}
            >
            <r.icon className="w-4 h-4 ml-2" / > {r.label}
            < /Button >
        ))}
        < /div >
        < / div >
    )
}

function DynamicBackground({theme}) {
    const imageUrl = theme == = 'dark' ? '/dark_background.jpg': '/light_background.jpg'
    return (
        < div
        className="fixed inset-0 -z-10 bg-cover bg-center transition-all duration-1000"
        style={{backgroundImage: `url('${imageUrl}')`}}
        >
        <div className="absolute inset-0 bg-black/30 dark:bg-black/60" > </div >
        < / div >
    )
}

// == == == == == == == == == == = Calculators == == == == == == == == == == = //

function LoanCalculator({params}) {
    const[P, setP] = useState(Number(params.p ?? 20000000));
    const[rate, setRate] = useState(Number(params.rate ?? 18));
    const[months, setMonths] = useState(Number(params.n ?? 24));

    const {monthly, totalPay, totalInterest} = useMemo(()=> {
        const r = (rate / 100) / 12;
        const n = Number(months);
        const p = Number(P);
        if (n <= 0 | | p <= 0) return {monthly: 0, totalPay: 0, totalInterest: 0};
        if (r === 0) {
            const m= p / n;
            return {monthly: m, totalPay: m * n, totalInterest: m * n - p};
        }
        const m = (p * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
        const tp = m * n;
        return {monthly: m, totalPay: tp, totalInterest: tp - p};
    }, [P, rate, months]);

    const shareParams = {p: P, rate, n: months};

    return (
        < Card className="rounded-2xl border-0 shadow-xl backdrop-blur bg-white/60 dark:bg-neutral-900/60" >
        < CardHeader className="flex flex-row items-center justify-between" >
        < div className="flex items-center gap-3" >
        < div className="p-2 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white" >
        < PiggyBank className="w-5 h-5" / >
        < /div >
        < CardTitle className="text-lg" > ماشین‌حساب قسط و وام < /CardTitle >
        < / div >
        < ActionRow type="loan" params={shareParams} results={{monthly, totalPay, totalInterest}} / >
        < /CardHeader >
        < CardContent className="space-y-4" >
        < div className="grid grid-cols-1 sm:grid-cols-3 gap-4" >
        < Field label="مبلغ وام" value={P} onChange={setP} / >
        < Field label="نرخ سود سالانه (%)" value={rate} onChange={setRate} / >
        < Field label="مدت بازپرداخت (ماه)" value={months} onChange={setMonths} / >
        < /div >
        < div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm" >
        < Stat title="قسط ماهانه" value={formatCurrency(monthly)} / >
        < Stat title="جمع پرداخت" value={formatCurrency(totalPay)} / >
        < Stat title="جمع سود" value={formatCurrency(totalInterest)} / >
        < /div >
        < / CardContent >
        < / Card >
    );
}

function SalaryOvertimeCalculator({params}) {
    const[hourly, setHourly] = useState(Number(params.h ?? 120000))
    const[regularHrs, setRegularHrs] = useState(Number(params.rh ?? 176))
    const[overtimeHrs, setOvertimeHrs] = useState(Number(params.oh ?? 20))
    const[multiplier, setMultiplier] = useState(Number(params.m ?? 1.4))

    const base = useMemo(()= > Number(hourly) * Number(regularHrs), [hourly, regularHrs])
    const ot = useMemo(()= > Number(hourly) * Number(overtimeHrs) * Number(multiplier), [hourly, overtimeHrs, multiplier])
    const total = base + ot

    const shareParams = {h: hourly, rh: regularHrs, oh: overtimeHrs, m: multiplier}

    return (
        < Card className="rounded-2xl border-0 shadow-xl backdrop-blur bg-white/60 dark:bg-neutral-900/60" >
        < CardHeader className="flex flex-row items-center justify-between" >
        < div className="flex items-center gap-3" >
        < div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white" >
        < Wallet className="w-5 h-5" / >
        < /div >
        < CardTitle className="text-lg" > محاسبه حقوق با اضافه‌کاری < /CardTitle >
        < / div >
        < ActionRow type="salary" params={shareParams} results={{total, base, ot}} / >
        < /CardHeader >
        < CardContent className="space-y-4" >
        < div className="grid grid-cols-1 sm:grid-cols-4 gap-4" >
        < Field label="دستمزد ساعتی (تومان)" value={hourly} onChange={setHourly} / >
        < Field label="ساعات عادی (ماه)" value={regularHrs} onChange={setRegularHrs} / >
        < Field label="ساعات اضافه‌کاری" value={overtimeHrs} onChange={setOvertimeHrs} / >
        < Field label="ضریب اضافه‌کاری" value={multiplier} onChange={setMultiplier} / >
        < /div >
        < div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm" >
        < Stat title="جمع حقوق ماه" value={formatCurrency(total)} / >
        < Stat title="حقوق عادی" value={formatCurrency(base)} / >
        < Stat title="اضافه‌کاری" value={formatCurrency(ot)} / >
        < /div >
        < / CardContent >
        < / Card >
    )
}

function BMICalculator({params}) {
    const[weight, setWeight] = useState(Number(params.w ?? 70))
    const[height, setHeight] = useState(Number(params.h ?? 175))

    const {bmi, status} = useMemo(()=> {
        const h= Number(height) / 100
        const b = h > 0 ? Number(weight) / (h * h): 0
        let s= "نامشخص"
        if (b > 0) {
            if (b < 18.5) s = "کم‌وزن"
            else if (b < 25) s= "نرمال"
            else if (b < 30) s= "اضافه‌وزن"
            else s= "چاق"
        }
        return {bmi: b, status: s}
    }, [weight, height])

    const shareParams = {w: weight, h: height}

    return (
        < Card className="rounded-2xl border-0 shadow-xl backdrop-blur bg-white/60 dark:bg-neutral-900/60" >
        < CardHeader className="flex flex-row items-center justify-between" >
        < div className="flex items-center gap-3" >
        < div className="p-2 rounded-xl bg-gradient-to-br from-rose-500 to-pink-600 text-white" >
        < Activity className="w-5 h-5" / >
        < /div >
        < CardTitle className="text-lg" > ماشین‌حساب BMI < /CardTitle >
        < / div >
        < ActionRow type="bmi" params={shareParams} results={{bmi, status}} / >
        < /CardHeader >
        < CardContent className="space-y-4" >
        < div className="grid grid-cols-1 sm:grid-cols-2 gap-4" >
        < Field label="وزن (کیلوگرم)" value={weight} onChange={setWeight} / >
        < Field label="قد (سانتی‌متر)" value={height} onChange={setHeight} / >
        < /div >
        < div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm" >
        < Stat title="شاخص BMI" value={formatNumber(bmi)} / >
        < Stat title="وضعیت" value={status} / >
        < /div >
        < / CardContent >
        < / Card >
    )
}

function VATCalculator({params}) {
    const[amount, setAmount] = useState(Number(params.a ?? 1000000))
    const[vat, setVat] = useState(Number(params.v ?? 9))

    const tax = useMemo(()= > (Number(amount) * Number(vat)) / 100, [amount, vat])
    const total = useMemo(()= > Number(amount) + tax, [amount, tax])

    const shareParams = {a: amount, v: vat}

    return (
        < Card className="rounded-2xl border-0 shadow-xl backdrop-blur bg-white/60 dark:bg-neutral-900/60" >
        < CardHeader className="flex flex-row items-center justify-between" >
        < div className="flex items-center gap-3" >
        < div className="p-2 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 text-white" >
        < Percent className="w-5 h-5" / >
        < /div >
        < CardTitle className="text-lg" > محاسبه مالیات بر ارزش افزوده < /CardTitle >
        < / div >
        < ActionRow type="vat" params={shareParams} results={{tax, total}} / >
        < /CardHeader >
        < CardContent className="space-y-4" >
        < div className="grid grid-cols-1 sm:grid-cols-2 gap-4" >
        < Field label="مبلغ کالا/خدمت" value={amount} onChange={setAmount} / >
        < Field label="درصد مالیات (%)" value={vat} onChange={setVat} / >
        < /div >
        < div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm" >
        < Stat title="مالیات" value={formatCurrency(tax)} / >
        < Stat title="قیمت بدون مالیات" value={formatCurrency(amount)} / >
        < Stat title="قیمت نهایی" value={formatCurrency(total)} / >
        < /div >
        < / CardContent >
        < / Card >
    )
}

function UnitConverter({params}) {
    const[tab, setTab] = useState(params.t ?? "length")
    return (
        < Card className="rounded-2xl border-0 shadow-xl backdrop-blur bg-white/60 dark:bg-neutral-900/60" >
        < CardHeader className="flex flex-row items-center justify-between" >
        < div className="flex items-center gap-3" >
        < div className="p-2 rounded-xl bg-gradient-to-br from-sky-500 to-blue-600 text-white" >
        < Ruler className="w-5 h-5" / >
        < /div >
        < CardTitle className="text-lg" > تبدیل واحدها < /CardTitle >
        < / div >
        < ActionRow type="convert" params={{t: tab}} / >
        < /CardHeader >
        < CardContent className="space-y-4" >
        < Tabs value={tab} onValueChange={setTab} className="w-full" >
        < TabsList className="grid grid-cols-3" >
        < TabsTrigger value="length" > طول < /TabsTrigger >
        < TabsTrigger value="weight" > وزن < /TabsTrigger >
        < TabsTrigger value="temp" > دما < /TabsTrigger >
        < / TabsList >
        < TabsContent value="length" > <LengthConverter / > < /TabsContent >
        < TabsContent value="weight" > <WeightConverter / > < /TabsContent >
        < TabsContent value="temp" > <TempConverter / > < /TabsContent >
        < / Tabs >
        < / CardContent >
        < / Card >
    )
}

function LengthConverter() {
    const[meters, setMeters] = useState(1)
    const km = useMemo(()= > Number(meters) / 1000, [meters])
    const cm = useMemo(()= > Number(meters) * 100, [meters])
    return (
        < div className="grid grid-cols-1 sm:grid-cols-3 gap-4" >
        < Field label="متر" value={meters} onChange={setMeters} / >
        < Stat title="کیلومتر" value={`${formatNumber(km)} km`} / >
        < Stat title="سانتی‌متر" value={`${formatNumber(cm)} cm`} / >
        < /div >
    )
}
function WeightConverter() {
    const[kg, setKg] = useState(1)
    const g = useMemo(()= > Number(kg) * 1000, [kg])
    const lb = useMemo(()= > Number(kg) * 2.2046226218, [kg])
    return (
        < div className="grid grid-cols-1 sm:grid-cols-3 gap-4" >
        < Field label="کیلوگرم" value={kg} onChange={setKg} / >
        < Stat title="گرم" value={`${formatNumber(g)} g`} / >
        < Stat title="پوند" value={`${formatNumber(lb)} lb`} / >
        < /div >
    )
}
function TempConverter() {
    const[c, setC] = useState(25)
    const f = useMemo(()= > (Number(c) * 9) / 5 + 32, [c])
    return (
        < div className="grid grid-cols-1 sm:grid-cols-2 gap-4" >
        < Field label="سانتی‌گراد (°C)" value={c} onChange={setC} / >
        < Stat title="فارنهایت" value={`${formatNumber(f)} °F`} / >
        < /div >
    )
}

function Field({label, value, onChange}) {
    return (
        < div >
        < Label > {label} < /Label >
        < Input inputMode="decimal" value={value} onChange={(e)= > onChange(Number(e.target.value | | 0))} / >
        < /div >
    )
}

function ActionRow({type, params = {}, results = {}}) {
    const[message, setMessage] = useState('')
    const makeLink = () = > {
        const qs = new URLSearchParams(params).toString()
        # /${type}${qs ? `?${qs}` : ""}`;
        const url = `${window.location.origin}${window.location.pathname}
        return url
    }
    const copy = () = > {
        const link = makeLink()
        const textArea = document.createElement("textarea")
        textArea.value = link
        document.body.appendChild(textArea)
        textArea.select()
        try {
            document.execCommand('copy')
            setMessage("لینک کپی شد ✅")
        } catch(err) {
            console.error('Fallback: Oops, unable to copy', err)
            setMessage("کپی انجام نشد!")
        }
        document.body.removeChild(textArea)
        setTimeout(()= > setMessage(''), 2000)
    }
    const save = () = > {
        pushHistory({type, params, results})
        setMessage("در تاریخچه ذخیره شد ✅")
        setTimeout(()= > setMessage(''), 2000)
    }
    const clear = () = > {
        clearHistory()
        setMessage("تاریخچه پاک شد ✅")
        setTimeout(()=> setMessage(''), 2000)
    }

    return (
        < div className="flex items-center gap-2 relative" >
        {message & & < div className = "absolute -top-10 right-0 bg-gray-800 text-white text-xs px-2 py-1 rounded" > {message} < /div >}
        < Button size="sm" variant="secondary" className="rounded-lg" onClick={copy} > <LinkIcon className="w-4 h-4 ml-1"/>کپی لینک < /Button >
        < Button size="sm" variant="secondary" className="rounded-lg" onClick={save} > <Save className="w-4 h-4 ml-1"/>ذخیره < /Button >
        < Button size="sm" variant="ghost" className="rounded-lg" onClick={clear} > <Trash2 className="w-4 h-4 ml-1"/>پاک‌کردن تاریخچه < /Button >
        < / div >
    )
}

// == == == == == == == == == == = Extra Calculators == == == == == == == == == == = //

function pad(n){return String(n).padStart(2, "0")
                }

function DateConverter(){
    const[gy, setGy] = useState(2025)
    const[gm, setGm] = useState(8)
    const[gd, setGd] = useState(28)

    const j = useMemo(()= > toJalaali(gy, gm, gd), [gy, gm, gd])
    const h = useMemo(()= > gregorianToHijri(gy, gm, gd), [gy, gm, gd])

    const[jy, setJy] = useState(1404)
    const[jm, setJm] = useState(6)
    const[jd, setJd] = useState(6)

    const gFromJ = useMemo(()= > toGregorian(jy, jm, jd), [jy, jm, jd])

    const[hy, setHy] = useState(1447)
    const[hm, setHm] = useState(2)
    const[hd, setHd] = useState(3)
    const gFromH = useMemo(()= > hijriToGregorian(hy, hm, hd), [hy, hm, hd])

    return (
        < Card className="rounded-2xl border-0 shadow-xl backdrop-blur bg-white/60 dark:bg-neutral-900/60" >
        < CardHeader >
        < CardTitle className="text-lg" > تبدیل تاریخ: میلادی ⇄ شمسی ⇄ قمری(تقریبی) < /CardTitle >
        < / CardHeader >
        < CardContent className="space-y-5 text-sm" >
        < div className="grid grid-cols-1 md:grid-cols-3 gap-4" >
        < div >
        < div className="font-bold mb-2" > از میلادی →< /div >
        < Label > تاریخ میلادی(Y-M-D) < /Label >
        < div className="grid grid-cols-3 gap-2" >
        < Input value={gy} onChange={e= >setGy(Number(e.target.value | |0))} / >
        < Input value={gm} onChange={e= >setGm(Number(e.target.value | |0))} / >
        < Input value={gd} onChange={e= >setGd(Number(e.target.value | |0))} / >
        < /div >
        < / div >
        < Stat title="تاریخ شمسی" value={`${j.jy} /${pad(j.jm)} /${pad(j.jd)}`} / >
        < Stat title="تاریخ قمری (تقریبی)" value={`${h.hy} /${pad(h.hm)} /${pad(h.hd)}`} / >
        < /div >

        < div className="grid grid-cols-1 md:grid-cols-2 gap-6" >
        < div >
        < div className="font-bold mb-2" > از شمسی → میلادی < /div >
        < div className="grid grid-cols-3 gap-2" >
        < Input value={jy} onChange={e= >setJy(Number(e.target.value | |0))} / >
        < Input value={jm} onChange={e= >setJm(Number(e.target.value | |0))} / >
        < Input value={jd} onChange={e= >setJd(Number(e.target.value | |0))} / >
        < /div >
        < div className="mt-2 text-neutral-600" > نتیجه: {gFromJ.gy}/{pad(gFromJ.gm)}/{pad(gFromJ.gd)} < /div >
        < / div >

        < div >
        < div className="font-bold mb-2" > از قمری(تقریبی) → میلادی < /div >
        < div className="grid grid-cols-3 gap-2" >
        < Input value={hy} onChange={e= >setHy(Number(e.target.value | |0))} / >
        < Input value={hm} onChange={e= >setHm(Number(e.target.value | |0))} / >
        < Input value={hd} onChange={e= >setHd(Number(e.target.value | |0))} / >
        < /div >
        < div className="mt-2 text-neutral-600" > نتیجه: {gFromH.gy}/{pad(gFromH.gm)}/{pad(gFromH.gd)} < /div >
        < / div >
        < / div >

        < div className="text-xs text-neutral-500" >
        *تبدیل قمری تقریبی است و ممکن است ±۱ روز اختلاف داشته باشد.
        < /div >
        < / CardContent >
        < / Card >
    )
}

function AgeCalculator(){
    const[y, setY] = useState(2009)
    const[m, setM] = useState(3)
    const[d, setD] = useState(22)
    const[events, setEvents] = useState(null)
    const[isGeneratingEvents, setIsGeneratingEvents] = useState(false)

    function diff(from , to){
        let years = to.getFullYear() - from .getFullYear()
        let months = to.getMonth() - from .getMonth()
        let days = to.getDate() - from .getDate()

        if (days < 0) {
            const prevMonth = new Date(to.getFullYear(), to.getMonth(), 0).getDate()
            days += prevMonth
            months -= 1
        }
        if (months < 0) {
            months += 12
            years -= 1
        }
        return {years, months, days}
    }

    const now = new Date()
    const birth = useMemo(()= > new Date(y, m-1, d), [y, m, d])
    const {years, months, days} = useMemo(()= > diff(birth, now), [birth])

    const next = new Date(now.getFullYear(), m-1, d)
    if (next < now) next.setFullYear(now.getFullYear() + 1)
    const until = Math.ceil((next - now) / (1000*60*60*24))

    const handleGenerateEvents = async () = > {
        if (!y | | y < 1000 | | y > new Date().getFullYear()) {
            setEvents("لطفا یک سال تولد معتبر وارد کنید.")
            return
        }
        setIsGeneratingEvents(true)
        setEvents(null)

        const prompt = `مهم‌ترین وقایع جهانی(سیاسی، علمی، فرهنگی، ورزشی) که در سال ${y} میلادی رخ داده‌اند را به صورت یک لیست کوتاه و جذاب به زبان فارسی بنویس.`

        try {
            const generatedText = await callGemini(prompt)
            setEvents(generatedText)
        } catch(error) {
            console.error("Error generating events:", error)
            setEvents("متاسفانه در دریافت اطلاعات خطایی رخ داد.")
        } finally {
            setIsGeneratingEvents(false)
        }
    }

    return (
        < Card className="rounded-2xl border-0 shadow-xl backdrop-blur bg-white/60 dark:bg-neutral-900/60" >
        < CardHeader > <CardTitle className="text-lg" > محاسبه سن دقیق < /CardTitle > </CardHeader >
        < CardContent className="space-y-4 text-sm" >
        < div className="grid grid-cols-3 gap-3" >
        < div > <Label > سال < /Label > <Input value={y} onChange={e = >setY(Number(e.target.value | |0))} / > < /div >
        < div > <Label > ماه < /Label > <Input value={m} onChange={e = >setM(Number(e.target.value | |0))} / > < /div >
        < div > <Label > روز < /Label > <Input value={d} onChange={e = >setD(Number(e.target.value | |0))} / > < /div >
        < / div >
        < div className="grid grid-cols-3 gap-4" >
        < Stat title="سال" value={years} / >
        < Stat title="ماه" value={months} / >
        < Stat title="روز" value={days} / >
        < /div >
        < div className="text-neutral-600" > روزهای مانده تا تولد بعدی: < b > {until} < /b > </div >
        < div className="pt-2" >
        < Button onClick={handleGenerateEvents} disabled={isGeneratingEvents} className="w-full" >
        < Sparkles className="w-4 h-4 ml-2" / >
        {isGeneratingEvents ? "در حال سفر در زمان...": "وقایع مهم سال تولد من"}
        < /Button >
        < / div >
        {isGeneratingEvents & & < div className = "text-center text-xs text-neutral-500 py-2" > درحال جستجو در تاریخ... < /div > }
        {events & & (
            < motion.div
            initial={{opacity: 0, y: -10}}
            animate={{opacity: 1, y: 0}}
            className="mt-4 p-4 rounded-lg border bg-white/50 dark:bg-neutral-800/50" >
            < h3 className="font-bold mb-2" > رویدادهای مهم سال {y} < /h3 >
            < div className="text-sm dark:text-neutral-300 max-w-none whitespace-pre-wrap leading-relaxed" > {events} < /div >
            < / motion.div >
        )}
        < /CardContent >
        < / Card >
    )
}

function DiscountCalculator(){
    const[price, setPrice] = useState(100000)
    const[percent, setPercent] = useState(20)

    const off = useMemo(()=> price * (percent/100), [price, percent])
    const final = useMemo(()=> price - off, [price, off])

    return (
        < Card className="rounded-2xl border-0 shadow-xl backdrop-blur bg-white/60 dark:bg-neutral-900/60" >
        < CardHeader > <CardTitle className="text-lg" > ماشین‌حساب تخفیف < /CardTitle > </CardHeader >
        < CardContent className="space-y-4 text-sm" >
        < div className="grid grid-cols-2 gap-3" >
        < div > <Label > قیمت اولیه < /Label > <Input inputMode="decimal" value={price} onChange={e = >setPrice(Number(e.target.value | |0))} / > < /div >
          < div > <Label > درصد تخفیف (% ) < /Label > <Input inputMode="decimal" value={percent} onChange={e = >setPercent(Number(e.target.value||0))} / > < /div >
        < / div >
        < div className="grid grid-cols-3 gap-4" >
          < Stat title="مبلغ تخفیف" value={formatCurrency(off)} / >
          < Stat title="قیمت نهایی" value={formatCurrency(final)} / >
          < Stat title="صرفه‌جویی" value={formatCurrency(off)} / >
        < /div >
        < / CardContent >
        < / Card >
    )
}

function BillSplitter(){
    const[total, setTotal] = useState(800000)
    const[people, setPeople] = useState(4)
    const[tip, setTip] = useState(10)
    const[tax, setTax] = useState(0)

    const tipAmt = useMemo(()=> total * (tip/100), [total, tip])
    const taxAmt = useMemo(()=> total * (tax/100), [total, tax])
    const final = total + tipAmt + taxAmt
    const each = useMemo(()= > (people > 0? final/people: 0), [final, people])

    const formatCurrencyLocal = (n) = > `${new Intl.NumberFormat("fa-IR", {maximumFractionDigits: 0}).format(isNaN(n)?0: n)} تومان`

    return (
        < Card className="rounded-2xl border-0 shadow-xl backdrop-blur bg-white/60 dark:bg-neutral-900/60" >
        < CardHeader > <CardTitle className="text-lg" > تقسیم صورت‌حساب < /CardTitle > </CardHeader >
        < CardContent className="space-y-4 text-sm" >
        < div className="grid grid-cols-2 md:grid-cols-4 gap-3" >
        < div > <Label > مبلغ کل < /Label > <Input inputMode="decimal" value={total} onChange={e= >setTotal(Number(e.target.value | |0))}/> < /div >
        < div > <Label > تعداد افراد < /Label > <Input inputMode="decimal" value={people} onChange={e= >setPeople(Number(e.target.value | |0))}/> < /div >
          < div > <Label > انعام ( % ) < /Label > <Input inputMode="decimal" value={tip} onChange={e = >setTip(Number(e.target.value||0))}/> < /div >
          < div > <Label > مالیات ( % ) < /Label > <Input inputMode="decimal" value={tax} onChange={e = >setTax(Number(e.target.value||0))}/> < /div >
        < / div >
        < div className="grid grid-cols-2 md:grid-cols-4 gap-4" >
          < Stat title="مبلغ انعام" value={formatCurrencyLocal(tipAmt)} / >
          < Stat title="مبلغ مالیات" value={formatCurrencyLocal(taxAmt)} / >
          < Stat title="جمع نهایی" value={formatCurrencyLocal(final)} / >
          < Stat title="سهم هر نفر" value={formatCurrencyLocal(each)} / >
        < /div >
        < / CardContent >
        < / Card >
    )
}

function BMRCalculator(){
    const[sex, setSex] = useState("male")
    const[age, setAge] = useState(28)
    const[height, setHeight] = useState(175)
    const[weight, setWeight] = useState(70)
    const[activity, setActivity] = useState(1.55)
    const[mealPlan, setMealPlan] = useState(null)
    const[isGenerating, setIsGenerating] = useState(false)

    const bmr = useMemo(()=> {
        if (sex == = "male") return 10*weight + 6.25*height - 5*age + 5
        return 10*weight + 6.25*height - 5*age - 161
    }, [sex, age, height, weight])

    const tdee = useMemo(()=> bmr*activity, [bmr, activity])

    const handleGenerateMealPlan = async () = > {
        setIsGenerating(true)
        setMealPlan(null)

        const prompt = `بر اساس اطلاعات زیر، یک نمونه برنامه غذایی یک روزه(صبحانه، ناهار، شام و دو میان‌وعده) برای هر سه هدف ارائه بده:
        1. ** کالری برای کاهش وزن: ** ${formatNumber(tdee - 500)} کالری
        2. ** کالری برای حفظ وزن: ** ${formatNumber(tdee)} کالری
        3. ** کالری برای افزایش وزن: ** ${formatNumber(tdee + 300)} کالری

        برای هر وعده، چند گزینه غذایی سالم و رایج در ایران پیشنهاد بده. خروجی باید به زبان فارسی و با فرمت Markdown خوانا باشد. هر هدف را با یک تیتر ** bold ** مشخص کن.`

        try {
            const generatedText = await callGemini(prompt)
            const formattedText = generatedText
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace( /\n/g, '<br />')
            setMealPlan(formattedText)
        } catch(error) {
            console.error("Error generating meal plan:", error)
            setMealPlan(
                "متاسفانه در تولید برنامه غذایی خطایی رخ داد. لطفا دوباره تلاش کنید.")
        } finally {
            setIsGenerating(false)
        }
    }

    return (
        < Card className="rounded-2xl border-0 shadow-xl backdrop-blur bg-white/60 dark:bg-neutral-900/60" >
        < CardHeader > <CardTitle className="text-lg" > محاسبه BMR و کالری روزانه < /CardTitle > </CardHeader >
        < CardContent className="space-y-4 text-sm" >
        < div className="grid grid-cols-2 md:grid-cols-5 gap-3" >
        < div className="col-span-2 md:col-span-1" >
            < Label > جنسیت < /Label >
            < div className="flex gap-2 mt-1" >
        < button onClick={() = >setSex("male")} className={`w-full px-3 py-1.5 rounded-md border ${sex == ="male"?"bg-neutral-900 text-white dark:bg-white dark:text-neutral-900": ""}`} > مرد < /button >
        < button onClick={() = >setSex("female")} className={`w-full px-3 py-1.5 rounded-md border ${sex == ="female"?"bg-neutral-900 text-white dark:bg-white dark:text-neutral-900": ""}`} > زن < /button >
            < / div >
        < / div >
        < div > <Label > سن (سال) < /Label > <Input inputMode="decimal" value={age} onChange={e= >setAge(Number(e.target.value | |0))}/> < /div >
        < div > <Label > قد (سانتی‌متر) < /Label > <Input inputMode="decimal" value={height} onChange={e= >setHeight(Number(e.target.value | |0))}/> < /div >
        < div > <Label > وزن (کیلوگرم) < /Label > <Input inputMode="decimal" value={weight} onChange={e= >setWeight(Number(e.target.value | |0))}/> < /div >
        < div className="col-span-2 md:col-span-2" >
            < Label > سطح فعالیت < /Label >
            < select className="w-full mt-1 rounded-md border border-neutral-300 dark:border-neutral-700 bg-white/80 dark:bg-neutral-800/60 px-3 py-2"
        value={activity} onChange={e = >setActivity(Number(e.target.value))} >
        < option value={1.2} > بی‌تحرک < /option >
        < option value={1.375} > کم‌تحرک < /option >
        < option value={1.55} > متوسط < /option >
        < option value={1.725} > فعال < /option >
        < option value={1.9} > بسیار فعال < /option >
            < / select >
        < / div >
        < / div >
        < div className="grid grid-cols-2 md:grid-cols-4 gap-4" >
        < Stat title="BMR (کالری پایه)" value={formatNumber(bmr)} / >
        < Stat title="TDEE (نگهدارنده)" value={formatNumber(tdee)} / >
        < Stat title="کاهش وزن (−۵۰۰)" value={formatNumber(tdee-500)} / >
        < Stat title="افزایش وزن (+۳۰۰)" value={formatNumber(tdee+300)} / >
        < /div >
        < div className="pt-2" >
            < Button onClick={handleGenerateMealPlan} disabled={isGenerating} className="w-full" >
        < Sparkles className="w-4 h-4 ml-2" / >
        {isGenerating ? "در حال تولید برنامه...": "دریافت برنامه غذایی هوشمند"}
        < /Button >
        < / div >
        {isGenerating & & < div className = "text-center text-xs text-neutral-500 py-2" > درحال مشورت با هوش مصنوعی برای تنظیم بهترین برنامه... < /div > }
        {mealPlan & & (
            < motion.div
            initial={{opacity: 0, y: -10}}
            animate={{opacity: 1, y: 0}}
            className="mt-4 p-4 rounded-lg border bg-white/50 dark:bg-neutral-800/50" >
            < h3 className="font-bold mb-2" > نمونه برنامه غذایی تولید شده با هوش مصنوعی < /h3 >
            < div className="text-sm dark:text-neutral-300 max-w-none leading-relaxed" dangerouslySetInnerHTML={{__html: mealPlan}} > </div >
            < / motion.div >
        )}
        < /CardContent >
        < / Card >
    )
}

function CurrencyWidget(){
    const SYMBOLS = [
        {key: "usd_sell", label: "دلار (فروش)"}, {key: "eur", label: "یورو"},
        {key: "gbp", label: "پوند"}, {key: "aed_sell",
                                      label: "درهم"}, {key: "try", label: "لیر"},
    ];

    const [toman, setToman] = useState(() = > {const saved = localStorage.getItem('toman'); return saved != = null ? JSON.parse(saved): true;});
    const [symbol, setSymbol] = useState(()= > localStorage.getItem("curr_symbol") | | "usd_sell");
    const [range, setRange] = useState(()= > Number(localStorage.getItem("curr_range") | | 30));
    const[data, setData] = useState(null);
    const[last, setLast] = useState(null);
    const[loading, setLoading] = useState(false);
    const[error, setError] = useState("");

    const API_KEY = "freedUAp4tZ4VavpUXvv7Zr4qR1uQod2"; // Public free key

    const toTS = (daysAgo=0) = > {
        const d = new Date();
        d.setHours(23, 59, 59, 999);
        d.setDate(d.getDate() - daysAgo);
        return Math.floor(d.getTime()/1000);
    }

    const fetchData = async (currentSymbol, currentRange) = > {
        setLoading(true);
        setError("");
        try {
            const latestUrl = `https: // api.navasan.tech/latest /?api_key =${API_KEY}`;
            const ohlcUrl = `https: // api.navasan.tech/ohlcSearch /?api_key =${API_KEY} & item =${currentSymbol} & start =${toTS(currentRange)} & end =${toTS(0)}`;

            const[latestRes, ohlcRes] = await Promise.all([fetch(latestUrl), fetch(ohlcUrl)]);

            if (!latestRes.ok | | !ohlcRes.ok) throw new Error("Network response was not ok");

            const latestData = await latestRes.json();
            const ohlcData = await ohlcRes.json();

            setData({latest: latestData, ohlc: ohlcData});
            setLast(new Date());
        } catch(e) {
            setError("خطا در دریافت نرخ‌ها. لطفاً بعداً تلاش کنید.");
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(()=> {
        fetchData(symbol, range);
        const id= setInterval(() = > fetchData(symbol, range), 60 * 60 * 1000); // Refresh every hour
        return ()= > clearInterval(id);
    }, [symbol, range]);

    useEffect(() = > {localStorage.setItem('toman', JSON.stringify(toman));}, [toman]);
    useEffect(() = > {localStorage.setItem('curr_symbol', symbol);}, [symbol]);
    useEffect(() = > {localStorage.setItem('curr_range', String(range));}, [range]);

    const list = useMemo(()=> {
        if (!data?.latest) return [];
        return SYMBOLS.map(it= > ({
            ...it,
            value: data.latest[it.key]?.value ? Number(data.latest[it.key].value): null,
            change: data.latest[it.key]?.change ? Number(data.latest[it.key].change): 0,
        }));
    }, [data]);

    const chartData = useMemo(()=> {
        return (Array.isArray(data?.ohlc) ? data.ohlc: []).map(row= > ({
            x: new Date(row.timestamp * 1000).toLocaleDateString('fa-IR', {day: 'numeric', month: 'short'}),
            close: Number(row.close)
        })).reverse();
    }, [data]);

    const formatCurrencyDisplay = (n) = > toman ? `${formatNumber(n)} تومان`: `${formatNumber(n * 10)} ریال`;

    const getStatBackground = (change) = > {
        if (change > 0) return "bg-gradient-to-br from-green-500/10 to-green-500/0 border-green-500/30 dark:from-green-500/20 dark:to-green-500/5 dark:border-green-500/40";
        if (change < 0) return "bg-gradient-to-br from-red-500/10 to-red-500/0 border-red-500/30 dark:from-red-500/20 dark:to-red-500/5 dark:border-red-500/40";
        return "bg-white/60 dark:bg-neutral-800/60 border-neutral-200 dark:border-neutral-700";
    };

    return (
        < Card className="rounded-2xl border-0 shadow-xl backdrop-blur bg-white/60 dark:bg-neutral-900/60" >
        < CardHeader >
        < div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4" >
        < CardTitle className="text-lg" > نرخ ارز < /CardTitle >
        < div className="flex flex-wrap items-center gap-2" >
        < select value={symbol} onChange={e = > setSymbol(e.target.value)} className="rounded-md border border-neutral-300 dark:border-neutral-700 bg-white/80 dark:bg-neutral-800/60 px-2 py-1 text-sm" >
        {SYMBOLS.map(s = > <option key={s.key} value={s.key} > {s.label} < /option > )}
        < /select >
        < select value={range} onChange={e = > setRange(Number(e.target.value))} className="rounded-md border border-neutral-300 dark:border-neutral-700 bg-white/80 dark:bg-neutral-800/60 px-2 py-1 text-sm" >
        < option value={7} > ۷ روز < /option > <option value={30} > ۳۰ روز < /option > <option value={90} > ۹۰ روز < /option >
        < / select >
        < label className="text-xs text-neutral-600 inline-flex items-center gap-2" > <input type="checkbox" checked={toman} onChange={e= > setToman(e.target.checked)} / > تومان < /label >
        < Button variant="secondary" size="sm" onClick={()= > fetchData(symbol, range)} disabled={loading} > {loading ? '...': 'به‌روزرسانی'} < /Button >
        < / div >
        < / div >
        < / CardHeader >
        < CardContent className="space-y-4 text-sm" >
        {error & & < div className = "text-red-500 p-2 rounded-md bg-red-500/10" > {error} < /div > }
        < div className="grid grid-cols-2 md:grid-cols-5 gap-3" >
        {list.map(it=> (
            < div key={it.key} className={`p-3 rounded-lg border transition-all duration-300 ${getStatBackground(it.change)}`} >
            < div className="text-xs text-neutral-500 dark:text-neutral-400" > {it.label} < /div >
            < div className="font-bold text-base" > {it.value ? formatCurrencyDisplay(it.value): "—"} < /div >
            < div className={`text-xs font-mono ${it.change > 0 ? 'text-green-600 dark:text-green-400': it.change < 0 ? 'text-red-600 dark:text-red-400': 'text-neutral-500'}`} >
            {it.change > 0 ? '▲': it.change < 0 ? '▼': ''} {formatNumber(Math.abs(it.change))}
            < /div >
            < / div >
        ))}
        < /div >
        < div className="h-64 w-full rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white/60 dark:bg-neutral-900/60 p-2" >
        {chartData.length > 0 ? (
            < ResponsiveContainer width="100%" height="100%" >
            < AreaChart data={chartData} >
                        < defs > <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1" > <stop offset="5%" stopColor="currentColor" stopOpacity={0.3}/> < stop offset="95%" stopColor="currentColor" stopOpacity={0}/> < /linearGradient > </defs >
                        < CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} / >
                        < XAxis dataKey="x" tick={{fontSize: 10}} / >
                        < YAxis domain={['dataMin - 100', 'dataMax + 100']} tick={{fontSize: 10}} tickFormatter={v = > formatNumber(toman ? v: v * 10)} / >
                        < Tooltip contentStyle={{backgroundColor: 'rgba(30,30,30,0.8)', border: 'none', borderRadius: '0.5rem'}} formatter={v= > [formatCurrencyDisplay(v), 'قیمت']} / >
                        < Area type="monotone" dataKey="close" stroke="currentColor" fillOpacity={1} fill="url(#g1)" / >
            < /AreaChart >
            < / ResponsiveContainer >
        ): < div className = "text-neutral-500 p-4 flex items-center justify-center h-full" > {loading ? 'در حال بارگذاری نمودار...': 'داده‌ای برای نمودار یافت نشد.'} < /div > }
        < /div >
        < div className="text-xs text-neutral-500" > آخرین به‌روزرسانی: {last ? last.toLocaleString("fa-IR"): "—"} < /div >
        < / CardContent >
        < / Card >
    );
}


// == == == == == == == == == == = Main App Component == == == == == == == == == == = //

export default function App() {
    const {theme, setTheme} = useTheme()
    const {route, params, navigate} = useHashRoute()

    useEffect(()=> {
        const titleMap = {
            home: "ماشین‌حساب‌های کاربردی", loan: "ماشین‌حساب قسط و وام", salary: "محاسبه حقوق",
            bmi: "ماشین‌حساب BMI", vat: "محاسبه مالیات", convert: "تبدیل واحدها", date: "تبدیل تاریخ",
            age: "محاسبه سن", discount: "محاسبه تخفیف", currency: "نرخ ارز", bill: "تقسیم صورتحساب",
            bmr: "BMR/کالری روزانه",
        }
        document.title = (titleMap[route] | | "ماشین‌حساب") + " | ابزارهای آنلاین"
    }, [route])

    const calculators = {
        loan: < LoanCalculator params = {params} / >,
        salary: < SalaryOvertimeCalculator params = {params} / >,
        bmi: < BMICalculator params = {params} / >,
        vat: < VATCalculator params = {params} / >,
        convert: < UnitConverter params = {params} / >,
        date: < DateConverter / >,
        age: < AgeCalculator / >,
        discount: < DiscountCalculator / >,
        currency: < CurrencyWidget / >,
        bill: < BillSplitter / >,
        bmr: < BMRCalculator / >,
    }

    return (
        < div dir="rtl" className="min-h-screen text-neutral-900 dark:text-neutral-100 font-[Vazirmatn,sans-serif]" >
        < DynamicBackground theme={theme} / >
        < main className="max-w-6xl mx-auto px-4 py-8" >
        < motion.div initial={{opacity: 0, y: 10}} animate={{opacity: 1, y: 0}} transition={{duration: 0.5}} >
        < HeaderBar
        theme={theme}
        onToggleTheme={()= > setTheme(theme == = "dark" ? "light": "dark")}
        current={route}
        onNav={(k)= > navigate(k)}
        / >

        < div className="space-y-6" >
        {route == = "home" ? (
            < div className="grid grid-cols-1 md:grid-cols-2 gap-6" >
            {Object.entries(calculators).map(([key, calculator])=> (
                < React.Fragment key={key} > {calculator} < /React.Fragment >
            ))}
            < /div >
        ): (
            calculators[route]
        )}
        < /div >

        < HistoryPanel / >

        < footer className="mt-10 text-center text-sm text-neutral-500 space-y-1" >
        < div > نسخه رایگان • بدون ثبت‌نام • هیچ داده‌ای به سرور ارسال نمی‌شود. < /div >
        < div >© {new Date().getFullYear()} < /div >
        < / footer >
        < / motion.div >
        < / main >
        < / div >
    )
}

function HistoryPanel() {
    const[open, setOpen] = useState(false)
    const[data, setData] = useState(readHistory())

    const handleClear = () = > {
        clearHistory()
        setData([])
    }

    return (
        < div className="mt-8" >
        < Button variant="outline" className="rounded-xl" onClick={()= > setOpen((s) = > !s)} >
        < History className="w-4 h-4 ml-2" / > تاریخچه محاسبات({data.length})
        < /Button >
        {open & & (
            < motion.div
            initial={{opacity: 0, height: 0}}
            animate={{opacity: 1, height: 'auto'}}
            className="mt-4 p-4 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white/60 dark:bg-neutral-900/60 overflow-hidden" >
            {data.length == = 0 ? (
                < div className="text-sm text-neutral-500" > هنوز چیزی ذخیره نشده. < /div >
            ): (
                < ul className="space-y-3 text-sm" >
                {data.map((it, i)=> (
                    < li key={i} className="flex items-start justify-between gap-3 p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800/50" >
                    < div >
                    < div className="font-bold" > {labelOfType(it.type)} < /div >
                    < div className="text-neutral-500 text-xs" > {new Date(it.ts).toLocaleString("fa-IR")} < /div >
                    < / div >
                    < Button size="sm" variant="secondary" className="rounded-lg" onClick={()= > {
                        const qs= new URLSearchParams(it.params).toString()
                        window.location.hash = `/${it.type}${qs ? `?${qs}`: ""}`
                    }} >
                    بارگذاری
                    < /Button >
                    < / li >
                ))}
                < /ul >
            )}
            < /motion.div >
        )}
        < /div >
    )
}

function labelOfType(t) {
    return ROUTES.find(r= > r.key == = t)?.label | | t
}
