import express from "express";
import fs from "fs";
import path from "path";
import cheerio from "cheerio";
import querystring from "querystring";
import { fileURLToPath } from "url";
import pkg from "pg";

const { Client } = pkg;

// ------------------------------
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// --------------------------------
// EXPRESS APP
// --------------------------------
const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// --------------------------------
// PANEL CONFIG
// --------------------------------
const PANEL_HOST = process.env.PANEL_HOST || "http://51.89.99.105";
const LOGIN_PATH = process.env.LOGIN_PATH || "/NumberPanel/login";

const PANEL_USER = process.env.PANEL_USER || "Junaidniz786";
const PANEL_PASS = process.env.PANEL_PASS || "Junaidniz786";

const PORT = process.env.PORT || 3001;
const TIMEOUT_MS = parseInt(process.env.TIMEOUT_MS || "15000");

// --------------------------------
// POSTGRES SESSION STORE
// --------------------------------

async function getPg() {
    const c = new Client({
        connectionString: process.env.DATABASE_URL,
        ssl: { rejectUnauthorized: false }
    });
    await c.connect();
    return c;
}

async function initDB() {
    try {
        const pg = await getPg();
        await pg.query(`
            CREATE TABLE IF NOT EXISTS session_store (
                id TEXT PRIMARY KEY,
                value TEXT
            )
        `);
        await pg.end();
    } catch (e) {
        console.log("DB Init Err:", e);
    }
}

await initDB();

// load cookie
async function loadCookie() {
    try {
        const pg = await getPg();
        const r = await pg.query("SELECT value FROM session_store WHERE id='session'");
        await pg.end();
        if (r.rows[0]) return r.rows[0].value;
    } catch {}
    return null;
}

// save cookie
async function saveCookie(v) {
    try {
        const pg = await getPg();
        await pg.query(
            "INSERT INTO session_store (id, value) VALUES ('session', $1) ON CONFLICT (id) DO UPDATE SET value=$1",
            [v]
        );
        await pg.end();
    } catch (e) {
        console.log("save err", e);
    }
}

function maskCookie(c) {
    if (!c) return null;
    return c.split(";")
        .map(p => {
            const [k, v] = p.split("=");
            if (!v) return p;
            return `${k}=****${v.slice(-3)}`;
        })
        .join("; ");
}

// -----------------------------------------------------
// FETCH WITH TIMEOUT
// -----------------------------------------------------
function timeoutSignal(ms) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), ms);
    return { controller, clear: () => clearTimeout(id) };
}

async function safeFetch(url, opts = {}) {
    const { controller, clear } = timeoutSignal(TIMEOUT_MS);
    try {
        const r = await fetch(url, { ...opts, signal: controller.signal });
        clear();
        return r;
    } catch (e) {
        clear();
        throw e;
    }
}

// ---------------------------------------
// LOGIN SYSTEM
// ---------------------------------------
async function performLogin() {
    try {
        const loginURL = PANEL_HOST + LOGIN_PATH;

        const page = await safeFetch(loginURL);
        const html = await page.text();

        const $ = cheerio.load(html);
        const form = $("form").first();

        const inputs = {};
        form.find("input").each((_, el) => {
            const n = $(el).attr("name");
            const v = $(el).attr("value") || "";
            if (n) inputs[n] = v;
        });

        let userField = Object.keys(inputs).find(n => /user|login/i.test(n));
        let passField = Object.keys(inputs).find(n => /pass|pwd/i.test(n));

        if (!userField || !passField) {
            console.log("Unable to detect login fields");
            return null;
        }

        inputs[userField] = PANEL_USER;
        inputs[passField] = PANEL_PASS;

        const body = querystring.stringify(inputs);

        const resp = await safeFetch(loginURL, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "PanelBot/1.0",
            },
            body,
            redirect: "manual"
        });

        let raw = [];
        if (resp.headers.raw) raw = resp.headers.raw()["set-cookie"] || [];
        else {
            const c = resp.headers.get("set-cookie");
            if (c) raw = [c];
        }

        if (!raw.length) return null;

        const cookie = raw.map(c => c.split(";")[0]).join("; ");

        await saveCookie(cookie);
        return cookie;

    } catch (err) {
        console.log("Login Err:", err);
        return null;
    }
}

// ---------------------------------------
// ROUTES
// ---------------------------------------

app.get("/", (req, res) => {
    res.json({ ok: true, msg: "API running" });
});

// ---------------------------------------
// LOGIN API
// ---------------------------------------
app.get("/api/login", async (req, res) => {
    const ck = await performLogin();
    if (!ck) return res.json({ ok: false, msg: "Login Failed" });

    res.json({ ok: true, cookie: maskCookie(ck) });
});

// ---------------------------------------
// FETCH NUMBERS
// ---------------------------------------
app.get("/api/numbers", async (req, res) => {
    let cookie = await loadCookie();
    if (!cookie) cookie = await performLogin();

    const url = `${PANEL_HOST}/NumberPanel/ints/agent/res/data_smsnumbers.php?frange=&fclient=&sEcho=2&iColumns=8&iDisplayStart=0&iDisplayLength=-1`;

    try {
        const r = await safeFetch(url, {
            headers: {
                Cookie: cookie,
                "User-Agent": "PanelBot/1.0"
            }
        });

        const txt = await r.text();
        res.send(txt);

    } catch (e) {
        res.json({ ok: false, err: e.toString() });
    }
});

// ---------------------------------------
// FETCH SMS
// ---------------------------------------
app.get("/api/sms", async (req, res) => {
    let cookie = await loadCookie();
    if (!cookie) cookie = await performLogin();

    const today = new Date().toISOString().split("T")[0];

    const url =
        `${PANEL_HOST}/NumberPanel/ints/agent/res/data_smscdr.php?` +
        `fdate1=${today}%2000:00:00&fdate2=${today}%2023:59:59&frange=&fclient=&fnum=&fcli=&fg=0&iColumns=9&iDisplayStart=0&iDisplayLength=-1`;

    try {
        const r = await safeFetch(url, {
            headers: {
                Cookie: cookie,
                "User-Agent": "PanelBot/1.0"
            }
        });

        const txt = await r.text();
        res.send(txt);

    } catch (e) {
        res.json({ ok: false, err: e.toString() });
    }
});

// ---------------------------------------
// START SERVER
// ---------------------------------------
app.listen(PORT, () => {
    console.log("API Running on port:", PORT);
});
