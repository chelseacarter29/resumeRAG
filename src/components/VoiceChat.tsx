// src/components/VoiceChat.tsx
import * as React from "react"

type Msg = { role: "user" | "assistant"; text: string }

export default function VoiceChat({
    endpoint = "http://localhost:8000/query", // <-- FastAPI endpoint only
    onResponse,
    transcript: externalTranscript,
    setTranscript: externalSetTranscript,
    onSend,
}: {
    endpoint?: string
    onResponse?: (data: any) => void
    transcript?: string
    setTranscript?: (value: string) => void
    onSend?: () => void
}) {
    const [listening, setListening] = React.useState(false)
    const [internalTranscript, setInternalTranscript] = React.useState("")
    const [messages, setMessages] = React.useState<Msg[]>([])
    const [sending, setSending] = React.useState(false)
    const recRef = React.useRef<SpeechRecognition | null>(null)
    
    const transcript = externalTranscript !== undefined ? externalTranscript : internalTranscript
    const setTranscript = externalSetTranscript || setInternalTranscript

    const start = () => {
        const SR: any =
            (window as any).webkitSpeechRecognition ||
            (window as any).SpeechRecognition
        if (!SR) {
            alert("Web Speech API not available in this browser")
            return
        }
        const rec: SpeechRecognition = new SR()
        rec.lang = "en-US"
        rec.interimResults = true
        rec.onresult = (e: SpeechRecognitionEvent) => {
            const r = e.results[e.results.length - 1]
            if (r && r[0]) setTranscript(r[0].transcript)
        }
        rec.onend = () => setListening(false)
        rec.start()
        recRef.current = rec
        setListening(true)
    }

    const stop = () => {
        recRef.current?.stop()
        setListening(false)
    }

    const send = async () => {
        const q = transcript.trim()
        if (!q || sending) return
        setSending(true)
        setMessages((m) => [...m, { role: "user", text: q }])
        setTranscript("")
        onSend?.()

        const body = {
            q,
            top_k: 8,
            mode: "auto",
            filters: { must_skills: [], should_skills: [], since_year: 2023 },
        }

        try {
            const res = await fetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            })
            const data = await res.json()

            onResponse?.(data)

            const answer = data?.answer ?? "No answer."
            setMessages((m) => [
                ...m,
                { role: "assistant", text: String(answer) },
            ])

            if ("speechSynthesis" in window && answer) {
                window.speechSynthesis.speak(
                    new SpeechSynthesisUtterance(String(answer))
                )
            }
        } catch (e) {
            console.error(e)
            setMessages((m) => [
                ...m,
                { role: "assistant", text: "Error contacting backend." },
            ])
        } finally {
            setSending(false)
        }
    }

    const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            send()
        }
    }

    return (
        <div style={{ padding: 16, borderRadius: 12, border: "1px solid #ddd" }}>
            <div style={{ display: "flex", gap: 8 }}>
                <button onClick={listening ? stop : start}>
                    {listening ? "Stop 🎙️" : "Speak 🎤"}
                </button>
                <button onClick={send} disabled={!transcript.trim() || sending}>
                    {sending ? "Sending…" : "Send"}
                </button>
            </div>

            <textarea
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
                onKeyDown={onKeyDown}
                rows={3}
                placeholder="Type or speak…"
                style={{ marginTop: 8, width: "100%", padding: 10, borderRadius: 8 }}
            />

            <div style={{ marginTop: 12 }}>
                {messages.map((m, i) => (
                    <div key={i} style={{ margin: "6px 0" }}>
                        <b>{m.role === "user" ? "You" : "Assistant"}:</b> {m.text}
                    </div>
                ))}
            </div>
        </div>
    )
}
