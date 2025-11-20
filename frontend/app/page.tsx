'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  const [apiStatus, setApiStatus] = useState<string>('checking...')
  const [healthData, setHealthData] = useState<any>(null)

  useEffect(() => {
    checkApiHealth()
  }, [])

  const checkApiHealth = async () => {
    try {
      const response = await axios.get(`${API_URL}/health`)
      setApiStatus('connected')
      setHealthData(response.data)
    } catch (error) {
      setApiStatus('disconnected')
      console.error('API connection error:', error)
    }
  }

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Wardrobe Auto
        </h1>
        <p className="text-xl text-gray-600">
          AI衣装管理・コーディネート自動化システム
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <a href="/wardrobe" className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
          <h3 className="text-lg font-semibold mb-2">ワードローブ管理</h3>
          <p className="text-gray-600 mb-4">
            手持ちの衣類を画像認識で自動登録・管理
          </p>
          <span className="inline-block px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
            ✓ 実装済み
          </span>
        </a>

        <a href="/outfits" className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
          <h3 className="text-lg font-semibold mb-2">AI コーディネート</h3>
          <p className="text-gray-600 mb-4">
            天候・予定に応じた最適なコーディネート提案
          </p>
          <span className="inline-block px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
            ✓ 実装済み
          </span>
        </a>

        <a href="/analysis" className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
          <h3 className="text-lg font-semibold mb-2">ワードローブ分析</h3>
          <p className="text-gray-600 mb-4">
            不足アイテムの分析とギャップ検出
          </p>
          <span className="inline-block px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
            ✓ 実装済み
          </span>
        </a>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">システムステータス</h3>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-gray-700">バックエンドAPI:</span>
            <span className={`px-3 py-1 rounded-full text-sm ${
              apiStatus === 'connected'
                ? 'bg-green-100 text-green-800'
                : apiStatus === 'checking...'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
            }`}>
              {apiStatus}
            </span>
          </div>
          {healthData && (
            <>
              <div className="flex justify-between items-center">
                <span className="text-gray-700">データベース:</span>
                <span className={`px-3 py-1 rounded-full text-sm ${
                  healthData.database === 'connected'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {healthData.database}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-700">Redis:</span>
                <span className={`px-3 py-1 rounded-full text-sm ${
                  healthData.redis === 'connected'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {healthData.redis}
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 p-6 rounded-lg">
        <h3 className="text-lg font-semibold mb-2 text-blue-900">
          実装完了機能
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-semibold text-blue-800 mb-2">✓ Phase 1-2: 基盤・画像処理</h4>
            <ul className="list-disc list-inside text-blue-800 space-y-1 text-sm">
              <li>Docker環境セットアップ</li>
              <li>PostgreSQL + pgvector</li>
              <li>YOLOv8 衣類検出</li>
              <li>CLIP 画像埋め込み</li>
              <li>rembg 背景除去</li>
              <li>属性自動抽出</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-blue-800 mb-2">✓ Phase 3-4: AI・分析</h4>
            <ul className="list-disc list-inside text-blue-800 space-y-1 text-sm">
              <li>vLLM コーディネート生成</li>
              <li>ルールエンジン</li>
              <li>天気API統合</li>
              <li>ワードローブギャップ分析</li>
              <li>組み合わせ計算</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
