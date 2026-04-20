import ImageUploader from './components/ImageUploader'

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>圖片去背</h1>
        <p>支援 PNG、JPG、WebP，最大 10 MB</p>
      </header>
      <main>
        <ImageUploader visible />
      </main>
    </div>
  )
}
