import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, LogOut } from 'lucide-react';
import { Message, Agent, StreamChunk } from '../types/chat';
import { chatAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

export const ChatInterface: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<Agent | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const currentStreamMessage = useRef<string>('');

  // Load agents on mount
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const data = await chatAPI.getAgents();
        setAgents(data.agents);
        // Set first agent as current
        if (data.agents.length > 0) {
          setCurrentAgent(data.agents[0]);
        }
      } catch (error) {
        toast.error('Failed to load agents');
        console.error('Error loading agents:', error);
      }
    };
    loadAgents();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isStreaming) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsStreaming(true);
    currentStreamMessage.current = '';

    // Create assistant message placeholder
    const assistantMessageId = `msg-${Date.now() + 1}`;
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      agentId: currentAgent?.slug,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, assistantMessage]);

    // Stream the response
    await chatAPI.streamChat(
      inputMessage,
      (chunk: StreamChunk) => {
        if (chunk.type === 'content' && chunk.content) {
          currentStreamMessage.current += chunk.content;
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: currentStreamMessage.current }
                : msg
            )
          );
        } else if (chunk.type === 'transfer') {
          // Handle agent transfer
          const newAgent = agents.find(a => a.slug === chunk.metadata?.to_agent);
          if (newAgent) {
            setCurrentAgent(newAgent);
            toast.success(`Transferred to ${newAgent.name}`);
          }
        } else if (chunk.type === 'error') {
          toast.error(chunk.content || 'An error occurred');
        }
      },
      sessionId,
      (error) => {
        toast.error('Failed to send message');
        console.error('Stream error:', error);
      }
    );

    setIsStreaming(false);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-semibold text-gray-800">RELATRIX Chat</h1>
            <div className="flex items-center space-x-4">
              {currentAgent && (
                <div className="flex items-center space-x-2">
                  <Bot className="w-5 h-5 text-blue-600" />
                  <span className="text-sm font-medium text-gray-700">{currentAgent.name}</span>
                </div>
              )}
              <div className="flex items-center space-x-2">
                {isAuthenticated ? (
                  <>
                    <User className="w-5 h-5 text-gray-600" />
                    <span className="text-sm text-gray-700">{user?.email}</span>
                    <button
                      onClick={async () => {
                        await logout();
                        navigate('/auth');
                      }}
                      className="ml-2 text-sm text-gray-500 hover:text-gray-700"
                      title="Logout"
                    >
                      <LogOut className="w-4 h-4" />
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => navigate('/auth')}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Login / Register
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Agent selector */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-2">
          <div className="flex space-x-2 overflow-x-auto">
            {agents.map(agent => (
              <button
                key={agent.slug}
                onClick={() => setCurrentAgent(agent)}
                className={`px-3 py-1 rounded-full text-sm whitespace-nowrap transition-colors ${
                  currentAgent?.slug === agent.slug
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {agent.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-10">
              <Bot className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p className="text-lg font-medium">Welcome to RELATRIX</p>
              <p className="text-sm mt-2">
                I'm {currentAgent?.name || 'your AI relationship counselor'}. How can I help you today?
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map(message => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`flex max-w-[80%] ${
                      message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                    }`}
                  >
                    <div
                      className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                        message.role === 'user' ? 'bg-blue-600 ml-2' : 'bg-gray-600 mr-2'
                      }`}
                    >
                      {message.role === 'user' ? (
                        <User className="w-5 h-5 text-white" />
                      ) : (
                        <Bot className="w-5 h-5 text-white" />
                      )}
                    </div>
                    <div
                      className={`px-4 py-2 rounded-lg ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-white border border-gray-200 text-gray-800'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                      {message.agentId && message.role === 'assistant' && (
                        <p className="text-xs mt-1 opacity-70">
                          {agents.find(a => a.slug === message.agentId)?.name}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {isStreaming && messages[messages.length - 1]?.content === '' && (
                <div className="flex justify-start">
                  <div className="bg-white border border-gray-200 rounded-lg px-4 py-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex space-x-2"
          >
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type your message..."
              disabled={isStreaming}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!inputMessage.trim() || isStreaming}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};