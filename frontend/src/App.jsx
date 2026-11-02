import { useState } from 'react'
import './App.css'

function App() {

  // =====================================
  // APPLICATION STATE
  // =====================================

  const [page, setPage] = useState('home')

  // Login information
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [authMode, setAuthMode] = useState('login')
  const [server, setServer] = useState('A')

  // WebSocket connection
  const [socket, setSocket] = useState(null)
  const [connectionStatus, setConnectionStatus] = useState("")

  // Chat information
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState([])

  // Group members received from the Python backend
  const [members, setMembers] = useState([])


  // =====================================
  // USER LOGIN
  // =====================================

  function handleLogin(event) {

    event.preventDefault()

    if (!username.trim() || !password) {
      alert('Enter your username and password.')
      return
    }

    if (socket && socket.readyState === WebSocket.OPEN) {
      alert('You are already connected.')
      return
    }

    setConnectionStatus('Connecting...')

    const newSocket = new WebSocket(
      'ws://localhost:8765'
    )

    newSocket.onopen = () => {

      newSocket.send(JSON.stringify({
        type: 'login',
        username: username.trim(),
        password: password,
        server: server
      }))

    }


    // RECEIVE DATA FROM PYTHON

    newSocket.onmessage = (event) => {

      const data = JSON.parse(event.data)

      console.log('Message received:', data)


      // REGISTERED GROUP MEMBERS

      if (data.type === 'group_members') {

        setMembers(data.members || [])

      }


      // PREVIOUS MESSAGE HISTORY

      else if (data.type === 'history') {

        setMessages(
          data.messages.map((msg) => ({
            id: msg.message_id,
            username: msg.username,
            server: msg.server || 'Network',
            message: msg.message,
            time: new Date(msg.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit'
            })
          }))
        )

      }


      // SUCCESSFUL CONNECTION

      else if (data.type === 'connected') {

        setSocket(newSocket)
        setConnectionStatus('Connected')
        setPage('chat')
        setPassword('')

        console.log(data.message)

      }


      // NEW CHAT MESSAGE

      else if (data.type === 'chat') {

        setMessages(previousMessages => [

          ...previousMessages,

          {
            id: Date.now() + Math.random(),
            username: data.username,
            server: data.server || 'Network',
            message: data.message,
            time: new Date().toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit'
            })
          }

        ])

      }


      // SERVER ERROR

      else if (data.type === 'error') {

        alert(data.message)

        setConnectionStatus('Connection failed')

        newSocket.close()

      }


      // SERVER DISCONNECTED

      else if (data.type === 'disconnect') {

        alert(data.message)

        setConnectionStatus('Disconnected')

      }

    }


    // CONNECTION ERROR

    newSocket.onerror = () => {

      console.error('WebSocket connection failed.')

      setConnectionStatus('Connection failed')

      alert('Could not connect to SkillCircle.')

    }


    // CONNECTION CLOSED

    newSocket.onclose = () => {

      setConnectionStatus('Disconnected')

      setSocket(null)

    }

  }


  // =====================================
  // USER REGISTRATION
  // =====================================

  function handleRegister(event) {

    event.preventDefault()

    if (!username.trim() || !password) {
      alert('Enter your username and password.')
      return
    }

    if (password.length < 8) {
      alert('Password must contain at least 8 characters.')
      return
    }

    const registerSocket = new WebSocket(
      'ws://localhost:8765'
    )

    registerSocket.onopen = () => {

      registerSocket.send(JSON.stringify({
        type: 'register',
        username: username.trim(),
        password: password
      }))

    }

    registerSocket.onmessage = (event) => {

      const data = JSON.parse(event.data)

      if (data.type === 'register_result') {

        alert(data.message)

        if (data.success) {

          setAuthMode('login')

          setPassword('')

        }

        registerSocket.close()

      }

    }

    registerSocket.onerror = () => {

      alert('Could not connect to SkillCircle.')

    }

  }


  // =====================================
  // SEND CHAT MESSAGE
  // =====================================

  function handleSendMessage(event) {

    event.preventDefault()

    if (!message.trim()) {
      return
    }

    if (!socket || socket.readyState !== WebSocket.OPEN) {

      alert('You are not connected to the chat server.')

      return

    }

    socket.send(JSON.stringify({

      type: 'message',

      message: message.trim()

    }))

    setMessage('')

  }


  // =====================================
  // LEAVE DISCUSSION ROOM
  // =====================================

  function handleLeaveChat() {

    if (socket) {
      socket.close()
    }

    setSocket(null)
    setConnectionStatus('Disconnected')
    setMessages([])
    setPage('home')

  }


  // =====================================
  // HOME PAGE
  // =====================================

  if (page === 'home') {

    return (

      <div className="app">

        <aside className="sidebar">

          <h2 className="logo">
            Skill<span>Circle.</span>
          </h2>

          <p className="menu-title">MENU</p>

          <nav>

            <button className="nav-link active">
              ⌂ Home
            </button>

          </nav>

          <div className="sidebar-bottom">

            <p>LEARNING TOGETHER</p>

            <h3>One skill at a time.</h3>

            <span>Knowledge grows when shared.</span>

          </div>

        </aside>


        <main className="main-content">

          <header className="topbar">

            <div>

              <p className="welcome">
                YOUR LEARNING COMMUNITY
              </p>

              <h1>Welcome to SkillCircle</h1>

              <p className="subtitle">
                Find your people. Share ideas. Learn something new.
              </p>

            </div>

          </header>


          {/* HERO SECTION */}

          <section className="hero">

            <div>

              <span className="hero-label">
                LEARN • CONNECT • GROW
              </span>

              <h2>
                Great things happen
                <br />
                when we learn together.
              </h2>

              <p>
                Join a community of curious minds, exchange ideas
                and grow your skills through meaningful discussions.
              </p>

              <button onClick={() => setPage('login')}>
                Explore learning groups →
              </button>

            </div>

            <div className="hero-decoration">
              S
            </div>

          </section>


          {/* LEARNING GROUPS */}

          <section className="groups-section">

            <div className="section-heading">

              <div>

                <p className="welcome">
                  FIND YOUR COMMUNITY
                </p>

                <h2>Learning Groups</h2>

              </div>

              <span>Explore all groups →</span>

            </div>


            <div className="group-grid">


              {/* JAVASCRIPT GROUP */}

              <div className="group-card javascript">

                <div className="group-icon">
                  JS
                </div>

                <span className="group-category">
                  PROGRAMMING
                </span>

                <h3>JavaScript Learners</h3>

                <p>
                  Learn JavaScript, solve problems and share
                  your coding journey with others.
                </p>

                <div className="group-footer">

                  <span>● Open group</span>

                  <button onClick={() => setPage('login')}>
                    Join group →
                  </button>

                </div>

              </div>


              {/* PYTHON GROUP */}

              <div className="group-card python">

                <div className="group-icon">
                  Py
                </div>

                <span className="group-category">
                  PROGRAMMING
                </span>

                <h3>Python Learners</h3>

                <p>
                  Explore Python programming and learn
                  through conversations and collaboration.
                </p>

                <div className="group-footer">

                  <span>Coming soon</span>

                  <button disabled>
                    Unavailable
                  </button>

                </div>

              </div>


              {/* DESIGN GROUP */}

              <div className="group-card design">

                <div className="group-icon">
                  UI
                </div>

                <span className="group-category">
                  DESIGN
                </span>

                <h3>UI/UX Designers</h3>

                <p>
                  Discuss creativity, user experiences
                  and beautiful digital interfaces.
                </p>

                <div className="group-footer">

                  <span>Coming soon</span>

                  <button disabled>
                    Unavailable
                  </button>

                </div>

              </div>

            </div>

          </section>


          <footer>
            SkillCircle © 2026 · Learn together. Grow together.
          </footer>

        </main>

      </div>

    )

  }


  // =====================================
  // LOGIN AND REGISTRATION PAGE
  // =====================================

  if (page === 'login') {

    return (

      <div className="login-page">

        <div className="login-card">

          <h2 className="logo">
            Skill<span>Circle.</span>
          </h2>

          <p className="welcome">
            JAVASCRIPT LEARNERS
          </p>

          <h1>
            {authMode === 'login'
              ? 'Welcome back!'
              : 'Create your account.'}
          </h1>

          <p className="login-description">
            {authMode === 'login'
              ? 'Enter your account details and choose a server to continue.'
              : 'Create your SkillCircle account to join the conversation.'}
          </p>


          <form onSubmit={
            authMode === 'login'
              ? handleLogin
              : handleRegister
          }>

            <label>Username</label>

            <input
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />


            <label>Password</label>

            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              minLength={8}
            />


            {authMode === 'login' && (

              <>
                <label>Select your server</label>

                <select
                  value={server}
                  onChange={(event) => setServer(event.target.value)}
                >

                  <option value="A">
                    Server A — Port 9001
                  </option>

                  <option value="B">
                    Server B — Port 9002
                  </option>

                </select>

              </>

            )}


            <button
              type="submit"
              className="connect-button"
            >

              {authMode === 'login'
                ? 'Login to SkillCircle →'
                : 'Create Account →'}

            </button>

          </form>


          <button
            type="button"
            className="back-button"
            onClick={() => {

              setAuthMode(
                authMode === 'login'
                  ? 'register'
                  : 'login'
              )

              setPassword('')

            }}
          >

            {authMode === 'login'
              ? 'New here? Create an account'
              : 'Already registered? Login'}

          </button>


          <button
            className="back-button"
            onClick={() => setPage('home')}
          >
            ← Back to groups
          </button>


          {connectionStatus && (
            <p className="connection-status-text">
              {connectionStatus}
            </p>
          )}

        </div>

      </div>

    )

  }


  // =====================================
  // JAVASCRIPT DISCUSSION ROOM
  // =====================================

  return (

    <div className="chat-layout">


      {/* LEFT SIDEBAR */}

      <aside className="chat-sidebar">

        <h2 className="logo">
          Skill<span>Circle.</span>
        </h2>

        <button
          className="back-button"
          onClick={handleLeaveChat}
        >
          ← Leave group
        </button>

        <p className="menu-title">
          YOUR GROUP
        </p>


        <div className="active-group">

          <div className="group-icon">
            JS
          </div>

          <div>

            <h3>JavaScript Learners</h3>

            <span>Group discussion</span>

          </div>

        </div>


        <div className="sidebar-bottom">

          <p>YOUR CONNECTION</p>

          <h3>{username}</h3>

          <span>
            Server {server}
          </span>

        </div>

      </aside>


      {/* CHAT AREA */}

      <main className="chat-main">


        {/* CHAT HEADER */}

        <header className="chat-header">

          <div>

            <p className="welcome">
              LEARNING COMMUNITY
            </p>

            <h2>JavaScript Learners</h2>

            <p className="subtitle">
              Learn, share and grow together.
            </p>

          </div>


          <div className="connection-status">

            <span className="status-dot"></span>

            {connectionStatus}

          </div>

        </header>


        {/* MESSAGE DISPLAY AREA */}

        <section className="messages-area">

          <div className="date-divider">

            <span>GROUP DISCUSSION</span>

          </div>


          {messages.length === 0 && (

            <div className="empty-chat">

              <h3>Welcome to JavaScript Learners!</h3>

              <p>
                Start the conversation. Share an idea,
                ask a question or say hello.
              </p>

            </div>

          )}


          {messages.map((msg) => (

            <div
              key={msg.id}
              className={
                msg.username === username
                  ? 'message-row own-message'
                  : 'message-row'
              }
            >

              <div className="message-avatar">

                {msg.username
                  ? msg.username.charAt(0).toUpperCase()
                  : '?'
                }

              </div>


              <div className="message-content">

                <div className="message-info">

                  <strong>
                    {msg.username}
                  </strong>

                  <span>
                    {msg.server === 'Network'
                      ? 'Distributed network'
                      : `Server ${msg.server}`
                    }
                  </span>

                  <small>
                    {msg.time}
                  </small>

                </div>


                <div className="message-bubble">

                  {msg.message}

                </div>

              </div>

            </div>

          ))}

        </section>


        {/* MESSAGE INPUT */}

        <form
          className="message-form"
          onSubmit={handleSendMessage}
        >

          <input
            type="text"
            placeholder="Write a message to the group..."
            value={message}
            onChange={(event) => setMessage(event.target.value)}
          />

          <button type="submit">
            Send →
          </button>

        </form>

      </main>


      {/* GROUP MEMBERS */}

      <aside className="members-panel">

        <h3>Group Members</h3>

        <p className="member-count">
          {members.length} {members.length === 1 ? 'member' : 'members'}
        </p>

        {members.length === 0 ? (
          <p>No members yet.</p>
        ) : (
          members.map((member) => (
            <div
              className="member-item"
              key={member.username}
            >
              <div className="member-avatar">
                {member.username.charAt(0).toUpperCase()}
              </div>

              <div className="member-details">
                <strong>{member.username}</strong>
              </div>
            </div>
          ))
        )}

      </aside>

    </div>

  )

}

export default App
