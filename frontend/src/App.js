import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState(null);
  const [referrals, setReferrals] = useState(null);
  const [loading, setLoading] = useState(true);
  const [webhookStatus, setWebhookStatus] = useState(null);
  const [usersboxTest, setUsersboxTest] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchStats();
    fetchUsers();
    fetchReferrals();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/stats`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/users`);
      const data = await response.json();
      setUsers(data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchReferrals = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/referrals`);
      const data = await response.json();
      setReferrals(data);
    } catch (error) {
      console.error('Error fetching referrals:', error);
    }
  };

  const setupWebhook = async () => {
    try {
      setWebhookStatus({ loading: true });
      const response = await fetch(`${API_BASE_URL}/api/set-webhook`, {
        method: 'POST'
      });
      const data = await response.json();
      setWebhookStatus(data);
    } catch (error) {
      setWebhookStatus({ status: 'error', message: error.message });
    }
  };

  const testUsersbox = async () => {
    try {
      setUsersboxTest({ loading: true });
      const response = await fetch(`${API_BASE_URL}/api/test-usersbox`, {
        method: 'POST'
      });
      const data = await response.json();
      setUsersboxTest(data);
    } catch (error) {
      setUsersboxTest({ status: 'error', message: error.message });
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-white"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 text-white">
      {/* Header */}
      <div className="bg-black/30 backdrop-blur-sm border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              🔍 Telegram Bot Dashboard
            </h1>
            <p className="mt-2 text-lg text-gray-300">
              Панель управления ботом для поиска по базам данных
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Setup Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Webhook Setup */}
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
            <h2 className="text-2xl font-semibold mb-4 flex items-center">
              🔗 Настройка Webhook
            </h2>
            <p className="text-gray-300 mb-4">
              Настройте webhook для получения сообщений от Telegram
            </p>
            <button
              onClick={setupWebhook}
              disabled={webhookStatus?.loading}
              className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 px-6 py-3 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              {webhookStatus?.loading ? 'Настройка...' : 'Настроить Webhook'}
            </button>
            
            {webhookStatus && !webhookStatus.loading && (
              <div className={`mt-4 p-4 rounded-lg ${
                webhookStatus.status === 'success' 
                  ? 'bg-green-500/20 border border-green-500/30' 
                  : 'bg-red-500/20 border border-red-500/30'
              }`}>
                <div className="font-medium">
                  {webhookStatus.status === 'success' ? '✅ Успешно!' : '❌ Ошибка'}
                </div>
                {webhookStatus.webhook_url && (
                  <div className="text-sm mt-2 text-gray-300">
                    URL: {webhookStatus.webhook_url}
                  </div>
                )}
                {webhookStatus.message && (
                  <div className="text-sm mt-2 text-gray-300">
                    {webhookStatus.message}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Usersbox Test */}
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
            <h2 className="text-2xl font-semibold mb-4 flex items-center">
              🔧 Тест Usersbox API
            </h2>
            <p className="text-gray-300 mb-4">
              Проверьте подключение к Usersbox API
            </p>
            <button
              onClick={testUsersbox}
              disabled={usersboxTest?.loading}
              className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 px-6 py-3 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              {usersboxTest?.loading ? 'Тестирование...' : 'Тестировать API'}
            </button>
            
            {usersboxTest && !usersboxTest.loading && (
              <div className={`mt-4 p-4 rounded-lg ${
                usersboxTest.status === 'success' 
                  ? 'bg-green-500/20 border border-green-500/30' 
                  : 'bg-red-500/20 border border-red-500/30'
              }`}>
                <div className="font-medium">
                  {usersboxTest.status === 'success' ? '✅ API работает!' : '❌ Ошибка API'}
                </div>
                {usersboxTest.data?.data?.balance !== undefined && (
                  <div className="text-sm mt-2 text-gray-300">
                    Баланс: {usersboxTest.data.data.balance} ₽
                  </div>
                )}
                {usersboxTest.message && (
                  <div className="text-sm mt-2 text-gray-300">
                    {usersboxTest.message}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-300">Всего сообщений</p>
                <p className="text-3xl font-bold">{stats?.total_messages || 0}</p>
              </div>
              <div className="text-4xl">💬</div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-300">Поисковых запросов</p>
                <p className="text-3xl font-bold">{stats?.total_searches || 0}</p>
              </div>
              <div className="text-4xl">🔍</div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-300">Пользователей</p>
                <p className="text-3xl font-bold">{stats?.total_users || 0}</p>
              </div>
              <div className="text-4xl">👥</div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-300">Рефералов</p>
                <p className="text-3xl font-bold">{stats?.total_referrals || 0}</p>
              </div>
              <div className="text-4xl">🎁</div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-300">Статус бота</p>
                <p className="text-lg font-bold text-green-400">Активен</p>
              </div>
              <div className="text-4xl">🤖</div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-8">
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-2 border border-white/20">
            <div className="flex space-x-2">
              {[
                { id: 'overview', label: '📊 Обзор', icon: '📊' },
                { id: 'users', label: '👥 Пользователи', icon: '👥' },
                { id: 'referrals', label: '🎁 Рефералы', icon: '🎁' },
                { id: 'activity', label: '📈 Активность', icon: '📈' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex-1 px-4 py-3 rounded-xl font-medium transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                      : 'text-gray-300 hover:text-white hover:bg-white/5'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Messages */}
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
              <h2 className="text-2xl font-semibold mb-4 flex items-center">
                💬 Последние сообщения
              </h2>
              <div className="space-y-3">
                {stats?.recent_messages?.slice(0, 5).map((message, index) => (
                  <div key={index} className="bg-white/5 rounded-lg p-3 border border-white/10">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-medium text-blue-300">
                        Chat ID: {message.chat_id}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded ${
                        message.direction === 'incoming' 
                          ? 'bg-green-500/20 text-green-300' 
                          : 'bg-blue-500/20 text-blue-300'
                      }`}>
                        {message.direction === 'incoming' ? '📥 Входящее' : '📤 Исходящее'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-300 mb-2 break-words">
                      {message.text?.length > 100 
                        ? message.text.substring(0, 100) + '...' 
                        : message.text
                      }
                    </p>
                    <p className="text-xs text-gray-400">
                      {formatDate(message.timestamp)}
                    </p>
                  </div>
                ))}
                {(!stats?.recent_messages || stats.recent_messages.length === 0) && (
                  <p className="text-gray-400 text-center py-4">Нет сообщений</p>
                )}
              </div>
            </div>

            {/* Recent Searches */}
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
              <h2 className="text-2xl font-semibold mb-4 flex items-center">
                🔍 Последние поиски
              </h2>
              <div className="space-y-3">
                {stats?.recent_searches?.slice(0, 5).map((search, index) => (
                  <div key={index} className="bg-white/5 rounded-lg p-3 border border-white/10">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-medium text-purple-300">
                        Chat ID: {search.chat_id}
                      </span>
                      <div className="flex space-x-2">
                        <span className="text-xs bg-purple-500/20 text-purple-300 px-2 py-1 rounded">
                          {search.results_count} результатов
                        </span>
                        {search.attempts_used && (
                          <span className="text-xs bg-red-500/20 text-red-300 px-2 py-1 rounded">
                            -{search.attempts_used} попытка
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="text-sm text-gray-300 mb-2 break-words font-mono bg-black/20 px-2 py-1 rounded">
                      {search.query}
                    </p>
                    <p className="text-xs text-gray-400">
                      {formatDate(search.timestamp)}
                    </p>
                  </div>
                ))}
                {(!stats?.recent_searches || stats.recent_searches.length === 0) && (
                  <p className="text-gray-400 text-center py-4">Нет поисков</p>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
            <h2 className="text-2xl font-semibold mb-4 flex items-center">
              👥 Пользователи бота
            </h2>
            <div className="space-y-3">
              {users?.users?.map((user, index) => (
                <div key={index} className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-medium text-blue-300">
                        {user.first_name || 'Без имени'} (@{user.username || 'нет'})
                      </h3>
                      <p className="text-sm text-gray-400">ID: {user.user_id}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-sm bg-green-500/20 text-green-300 px-2 py-1 rounded">
                        {user.free_attempts || 0} попыток
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-gray-400">Поиски</p>
                      <p className="font-medium">{user.total_searches || 0}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Рефералы</p>
                      <p className="font-medium">{user.total_referrals || 0}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Реф. код</p>
                      <p className="font-mono text-xs">{user.referral_code}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Регистрация</p>
                      <p className="text-xs">{formatDate(user.created_at)}</p>
                    </div>
                  </div>
                </div>
              ))}
              {(!users?.users || users.users.length === 0) && (
                <p className="text-gray-400 text-center py-8">Нет пользователей</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'referrals' && (
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
            <h2 className="text-2xl font-semibold mb-4 flex items-center">
              🎁 Реферальная активность
            </h2>
            <div className="space-y-3">
              {referrals?.referrals?.map((referral, index) => (
                <div key={index} className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <div className="flex justify-between items-center mb-2">
                    <div>
                      <p className="font-medium text-green-300">
                        Новый реферал
                      </p>
                      <p className="text-sm text-gray-400">
                        Реферер: {referral.referrer_id} → Новый: {referral.referred_id}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="text-sm bg-yellow-500/20 text-yellow-300 px-2 py-1 rounded">
                        {referral.referral_code}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400">
                    {formatDate(referral.timestamp)}
                  </p>
                </div>
              ))}
              {(!referrals?.referrals || referrals.referrals.length === 0) && (
                <p className="text-gray-400 text-center py-8">Нет рефералов</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'activity' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Users */}
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
              <h2 className="text-2xl font-semibold mb-4 flex items-center">
                🏆 Топ пользователей
              </h2>
              <div className="space-y-3">
                {stats?.top_users?.map((user, index) => (
                  <div key={index} className="bg-white/5 rounded-lg p-3 border border-white/10">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">
                          {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '🏅'}
                        </span>
                        <div>
                          <p className="font-medium">Chat ID: {user._id}</p>
                          <p className="text-sm text-gray-400">Поисков: {user.count}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                {(!stats?.top_users || stats.top_users.length === 0) && (
                  <p className="text-gray-400 text-center py-4">Нет данных</p>
                )}
              </div>
            </div>

            {/* Stats Summary */}
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
              <h2 className="text-2xl font-semibold mb-4 flex items-center">
                📈 Сводка
              </h2>
              <div className="space-y-4">
                <div className="bg-white/5 rounded-lg p-4">
                  <h3 className="font-medium text-blue-300 mb-2">Пользователи</h3>
                  <p className="text-2xl font-bold">{stats?.total_users || 0}</p>
                  <p className="text-sm text-gray-400">Зарегистрированных пользователей</p>
                </div>
                <div className="bg-white/5 rounded-lg p-4">
                  <h3 className="font-medium text-purple-300 mb-2">Активность</h3>
                  <p className="text-2xl font-bold">{stats?.total_searches || 0}</p>
                  <p className="text-sm text-gray-400">Выполненных поисков</p>
                </div>
                <div className="bg-white/5 rounded-lg p-4">
                  <h3 className="font-medium text-green-300 mb-2">Рефералы</h3>
                  <p className="text-2xl font-bold">{stats?.total_referrals || 0}</p>
                  <p className="text-sm text-gray-400">Успешных приглашений</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Bot Instructions */}
        <div className="mt-8 bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
          <h2 className="text-2xl font-semibold mb-4 flex items-center">
            📖 Как использовать бота
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-medium text-blue-300 mb-3">Команды бота:</h3>
              <ul className="space-y-2 text-gray-300">
                <li>• <code className="bg-black/30 px-2 py-1 rounded">/start</code> - Начать работу</li>
                <li>• <code className="bg-black/30 px-2 py-1 rounded">/search &lt;запрос&gt;</code> - Поиск</li>
                <li>• <code className="bg-black/30 px-2 py-1 rounded">/sources</code> - Список баз</li>
                <li>• <code className="bg-black/30 px-2 py-1 rounded">/balance</code> - Баланс</li>
                <li>• <code className="bg-black/30 px-2 py-1 rounded">/help</code> - Помощь</li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-medium text-purple-300 mb-3">Примеры поиска:</h3>
              <ul className="space-y-2 text-gray-300">
                <li>• <code className="bg-black/30 px-2 py-1 rounded">+79123456789</code> - По телефону</li>
                <li>• <code className="bg-black/30 px-2 py-1 rounded">example@mail.ru</code> - По email</li>
                <li>• <code className="bg-black/30 px-2 py-1 rounded">Иван Петров</code> - По имени</li>
                <li>• Любой текст для поиска</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Refresh Button */}
        <div className="mt-8 text-center">
          <button
            onClick={() => {
              fetchStats();
              fetchUsers();
              fetchReferrals();
            }}
            className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 px-8 py-3 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl"
          >
            🔄 Обновить данные
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;