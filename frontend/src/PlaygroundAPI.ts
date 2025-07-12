const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface PlaygroundRequest {
  agent_slug: string
  system_prompt: string
  message: string
  settings: {
    model: string
    temperature: number
    show_json: boolean
    enable_fallback: boolean
  }
}

interface PlaygroundResponse {
  clean_response: string
  raw_response: string
  detected_json: string | null
  agent_switch: string | null
  debug_info: {
    detected_json: string | null
    agent_switch: string | null
    token_count: number
    processing_time: string
    model_used: string
    fallback_triggered: boolean
  }
}

export async function testPlayground(request: PlaygroundRequest): Promise<PlaygroundResponse> {
  const response = await fetch(`${API_URL}/api/playground/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    throw new Error(`Playground request failed: ${response.statusText}`)
  }

  return response.json()
}