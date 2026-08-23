import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import client from '../api/client'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

export default function ChiTiet() {
  const { id } = useParams()
  const [cb, setCb] = useState(null)
  const [loading, setLoading] = useState(true)
  const { user } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    setLoading(true)
    client.get(`/can-bo/${id}`).then((res) => {
      setCb(res.data)
      setLoading(false)
    })
  }, [id])

  async function handleXoa() {
    if (!confirm('Xóa vĩnh viễn hồ sơ này?')) return
    await client.delete(`/can-bo/${id}`)
    navigate('/')
  }

  async function handleXuatDocx() {
    const res = await client.get(`/can-bo/${id}/xuat-docx`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `So_yeu_ly_lich_${cb.ho_ten_khai_sinh.replace(/\s/g, '_')}.docx`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  }

  if (loading) return <Layout><p>Đang tải...</p></Layout>
  if (!cb) return <Layout><p>Không tìm thấy hồ sơ.</p></Layout>

  return (
    <Layout>
      <Link to="/">← Về danh sách</Link>

      <div className="profile-head">
        <div className="avatar-lg">{cb.ho_ten_khai_sinh[0]}</div>
        <div style={{ flex: 1 }}>
          <h1>{cb.ho_ten_khai_sinh} {cb.ten_goi_khac && `(${cb.ten_goi_khac})`}</h1>
          <p className="meta">
            {cb.chuc_vu_ten || 'Chưa có chức vụ'} · {cb.don_vi_ten || 'Chưa gán đơn vị'}
            {cb.so_hieu_can_bo && ` · Số hiệu CB: ${cb.so_hieu_can_bo}`}
          </p>
        </div>
        <div className="actions">
          <button className="btn btn-outline btn-sm" onClick={handleXuatDocx}>📄 Xuất hồ sơ (.docx)</button>
          {(user.vai_tro === 'admin' || user.vai_tro === 'editor') && (
            <Link to={`/can-bo/${id}/sua`}><button className="btn btn-outline btn-sm">Sửa hồ sơ</button></Link>
          )}
          {user.vai_tro === 'admin' && (
            <button className="btn btn-danger btn-sm" onClick={handleXoa}>Xóa</button>
          )}
        </div>
      </div>

      <div className="card">
        <Section num="1" title="Thông tin cá nhân">
          <Field label="Giới tính" value={cb.gioi_tinh} />
          <Field label="Ngày sinh" value={cb.ngay_sinh} />
          <Field label="Nơi sinh" value={cb.noi_sinh} />
          <Field label="Quê quán" value={[cb.que_quan_xa, cb.que_quan_huyen, cb.que_quan_tinh].filter(Boolean).join(', ')} />
          <Field label="Nơi ở hiện nay" value={cb.noi_o_hien_nay} />
          <Field label="Điện thoại" value={cb.dien_thoai} />
          <Field label="Số CMND/CCCD" value={cb.so_cmnd_cccd} />
          <Field label="Dân tộc" value={cb.dan_toc} />
          <Field label="Tôn giáo" value={cb.ton_giao} />
        </Section>

        <Section num="4" title="Trình độ, chức vụ, ngạch lương">
          <Field label="Học hàm/học vị cao nhất" value={cb.hoc_ham_hoc_vi_cao_nhat} />
          <Field label="Chức vụ" value={cb.chuc_vu_ten} />
          <Field label="Lý luận chính trị" value={cb.ly_luan_chinh_tri} />
          <Field label="Ngạch/lương" value={cb.ngach_cong_chuc} />
          <Field label="Bậc lương / Hệ số" value={cb.bac_luong && `${cb.bac_luong} / ${cb.he_so_luong ?? ''}`} />
        </Section>

        <Section num="26" title="Đào tạo, bồi dưỡng">
          {cb.dao_tao.length === 0 ? <Empty /> : (
            <SimpleTable
              headers={['Tên trường', 'Ngành học', 'Thời gian', 'Hình thức', 'Văn bằng']}
              rows={cb.dao_tao.map((d) => [d.ten_truong, d.nganh_hoc, `${d.tu_nam ?? ''} – ${d.den_nam ?? ''}`, d.hinh_thuc_hoc, d.van_bang_chung_chi])}
            />
          )}
        </Section>

        <Section num="27" title="Quá trình công tác">
          {cb.qua_trinh_cong_tac.length === 0 ? <Empty /> : (
            <SimpleTable
              headers={['Từ', 'Đến', 'Chức danh, đơn vị công tác']}
              rows={cb.qua_trinh_cong_tac.map((q) => [q.tu_thang_nam, q.den_thang_nam, q.chuc_danh_don_vi])}
            />
          )}
        </Section>

        <div className="section-title"><span className="section-num">22</span>&nbsp;Khen thưởng &amp; <span className="section-num" style={{ marginLeft: 6 }}>23</span>&nbsp;Kỷ luật</div>
        <div className="field-grid">
          <div>
            <strong style={{ fontSize: 13, color: 'var(--ink-soft)' }}>Khen thưởng</strong>
            {cb.khen_thuong.length === 0 ? <Empty /> : (
              <ul style={{ margin: '8px 0 0', paddingLeft: 18 }}>
                {cb.khen_thuong.map((k, i) => <li key={i}>{k.noi_dung} ({k.nam})</li>)}
              </ul>
            )}
          </div>
          <div>
            <strong style={{ fontSize: 13, color: 'var(--ink-soft)' }}>Kỷ luật</strong>
            {cb.ky_luat.length === 0 ? <Empty /> : (
              <ul style={{ margin: '8px 0 0', paddingLeft: 18 }}>
                {cb.ky_luat.map((k, i) => <li key={i}>{k.hinh_thuc} — {k.ly_do} ({k.nam})</li>)}
              </ul>
            )}
          </div>
        </div>

        <Section num="30" title="Quan hệ gia đình">
          {cb.quan_he_gia_dinh.length === 0 ? <Empty /> : (
            <SimpleTable
              headers={['Nhóm', 'Quan hệ', 'Họ tên', 'Năm sinh', 'Thông tin']}
              rows={cb.quan_he_gia_dinh.map((g) => [g.nhom, g.quan_he, g.ho_ten, g.nam_sinh, g.thong_tin])}
            />
          )}
        </Section>
      </div>
    </Layout>
  )
}

// ---- component phụ ----
function Section({ num, title, children }) {
  return (
    <>
      <div className="section-title"><span className="section-num">{num}</span> {title}</div>
      <div className="field-grid cols-3">{children}</div>
    </>
  )
}

function Field({ label, value }) {
  return (
    <div className="field">
      <div className="k">{label}</div>
      <div className={`v ${!value ? 'empty' : ''}`}>{value || ''}</div>
    </div>
  )
}

function Empty() {
  return <p style={{ color: 'var(--ink-soft)' }}>—</p>
}

function SimpleTable({ headers, rows }) {
  return (
    <table style={{ gridColumn: '1 / -1' }}>
      <thead><tr>{headers.map((h) => <th key={h}>{h}</th>)}</tr></thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>{row.map((cell, j) => <td key={j}>{cell || '—'}</td>)}</tr>
        ))}
      </tbody>
    </table>
  )
}