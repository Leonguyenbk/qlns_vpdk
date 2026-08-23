import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import client from '../api/client'
import Layout from '../components/Layout'

export default function DanhSach() {
  const [dsCanBo, setDsCanBo] = useState([])
  const [donViList, setDonViList] = useState([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [donViId, setDonViId] = useState('')
  const [trangThai, setTrangThai] = useState('')
  const [chucVuList, setChucVuList] = useState([])
  const [chucVuId, setChucVuId] = useState('')

  useEffect(() => {
    client.get('/chuc-vu').then((res) => setChucVuList(res.data))
  }, [])

  useEffect(() => {
    client.get('/don-vi').then((res) => setDonViList(res.data))
  }, [])

  const taiDanhSach = useCallback(async () => {
    setLoading(true)
    const params = {}
    if (q) params.q = q
    if (donViId) params.don_vi_id = donViId
    if (chucVuId) params.chuc_vu_id = chucVuId
    if (trangThai) params.trang_thai = trangThai
    const res = await client.get('/can-bo', { params })
    setDsCanBo(res.data)
    setLoading(false)
  }, [q, donViId, chucVuId, trangThai])

  useEffect(() => { taiDanhSach() }, [taiDanhSach])

  function handleSubmit(e) {
    e.preventDefault()
    taiDanhSach()
  }

  function xoaLoc() {
    setQ(''); setDonViId(''); setChucVuId(''); setTrangThai('')
  }

  function tagClass(trangThai) {
    if (trangThai === 'Đang công tác') return 'tag tag-active'
    if (trangThai === 'Nghỉ hưu') return 'tag tag-leave'
    return 'tag tag-other'
  }

  return (
    <Layout>
      <div className="page-title">Tra cứu nhân sự</div>
      <div className="page-sub">Danh sách cán bộ, công chức, viên chức toàn Sở và các đơn vị trực thuộc.</div>

      <div className="stat-row">
        <div className="stat"><div className="num">{dsCanBo.length}</div><div className="label">Kết quả</div></div>
        <div className="stat"><div className="num">{donViList.length}</div><div className="label">Đơn vị</div></div>
      </div>

      <div className="card">
        <div className="toolbar">
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Tìm theo họ tên, số hiệu CB, CCCD, chức vụ..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
              style={{ minWidth: 280 }}
            />
            <select value={donViId} onChange={(e) => setDonViId(e.target.value)}>
              <option value="">— Tất cả đơn vị —</option>
              {donViList.map((dv) => <option key={dv.id} value={dv.id}>{dv.ten_don_vi}</option>)}
            </select>
            <select value={chucVuId} onChange={(e) => setChucVuId(e.target.value)}>
              <option value="">— Tất cả chức vụ —</option>
              {chucVuList.map((cv) => <option key={cv.id} value={cv.id}>{cv.ten_chuc_vu}</option>)}
            </select>
            <select value={trangThai} onChange={(e) => setTrangThai(e.target.value)}>
              <option value="">— Mọi trạng thái —</option>
              {['Đang công tác', 'Nghỉ hưu', 'Thôi việc', 'Chuyển công tác'].map((tt) => <option key={tt}>{tt}</option>)}
            </select>
            <button className="btn btn-primary" type="submit">Tìm kiếm</button>
            {(q || donViId || chucVuId || trangThai) && (
              <button type="button" className="btn btn-outline" onClick={xoaLoc}>Xóa lọc</button>
            )}
          </form>
        </div>

        {loading ? (
          <p>Đang tải...</p>
        ) : dsCanBo.length === 0 ? (
          <div className="empty-state">
            <div className="icon">🔍</div>
            <div>Không tìm thấy hồ sơ nào phù hợp.</div>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th></th><th>Họ và tên</th><th>Số hiệu CB</th><th>Đơn vị</th>
                <th>Chức vụ</th><th>Trạng thái</th><th></th>
              </tr>
            </thead>
            <tbody>
              {dsCanBo.map((cb) => (
                <tr key={cb.id}>
                  <td><div className="avatar-circle">{cb.ho_ten_khai_sinh[0]}</div></td>
                  <td className="name-cell"><Link to={`/can-bo/${cb.id}`}>{cb.ho_ten_khai_sinh}</Link></td>
                  <td>{cb.so_hieu_can_bo || '—'}</td>
                  <td>{cb.don_vi_ten || '—'}</td>
                  <td>{cb.chuc_vu_ten || '—'}</td>
                  <td><span className={tagClass(cb.trang_thai)}>{cb.trang_thai}</span></td>
                  <td><Link to={`/can-bo/${cb.id}`}><button className="btn btn-outline btn-sm">Xem</button></Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  )
}