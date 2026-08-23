import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import client from '../api/client'
import Layout from '../components/Layout'

const RONG = {
  ho_ten_khai_sinh: '', ten_goi_khac: '', gioi_tinh: '', ngay_sinh: '',
  noi_sinh: '', que_quan_xa: '', que_quan_huyen: '', que_quan_tinh: '',
  noi_o_hien_nay: '', dien_thoai: '', email: '', dan_toc: '', ton_giao: '',
  so_cmnd_cccd: '', don_vi_id: '', so_hieu_can_bo: '', chuc_vu_id: '',
  hoc_ham_hoc_vi_cao_nhat: '', ly_luan_chinh_tri: '',
  ngach_cong_chuc: '', bac_luong: '', he_so_luong: '', trang_thai: 'Đang công tác',
  dao_tao: [], qua_trinh_cong_tac: [], khen_thuong: [], ky_luat: [], quan_he_gia_dinh: [],
}

export default function Form() {
  const { id } = useParams() // undefined nếu là "thêm mới"
  const isEdit = Boolean(id)
  const navigate = useNavigate()

  const [form, setForm] = useState(RONG)
  const [donViList, setDonViList] = useState([])
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [chucVuList, setChucVuList] = useState([])
  useEffect(() => {
    client.get('/chuc-vu').then((res) => setChucVuList(res.data))
    }, [])

  useEffect(() => {
    client.get('/don-vi').then((res) => setDonViList(res.data))
  }, [])

  useEffect(() => {
    if (!isEdit) return
    client.get(`/can-bo/${id}`).then((res) => {
      const d = res.data
      setForm({
        ...RONG,
        ...d,
        don_vi_id: d.don_vi_id || '',
        he_so_luong: d.he_so_luong ?? '',
      })
      setLoading(false)
    })
  }, [id, isEdit])

  function setField(name, value) {
    setForm((f) => ({ ...f, [name]: value }))
  }

  // ---- helpers cho các mục lặp (đào tạo, công tác, khen thưởng, kỷ luật, gia đình) ----
  function addRow(key, rongItem) {
    setForm((f) => ({ ...f, [key]: [...f[key], rongItem] }))
  }
  function removeRow(key, index) {
    setForm((f) => ({ ...f, [key]: f[key].filter((_, i) => i !== index) }))
  }
  function updateRow(key, index, field, value) {
    setForm((f) => ({
      ...f,
      [key]: f[key].map((row, i) => (i === index ? { ...row, [field]: value } : row)),
    }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = { ...form, don_vi_id: form.don_vi_id || null }
      let res
      if (isEdit) {
        res = await client.put(`/can-bo/${id}`, payload)
      } else {
        res = await client.post('/can-bo', payload)
      }
      navigate(`/can-bo/${res.data.id}`)
    } catch (err) {
      setError(err.response?.data?.error || 'Có lỗi khi lưu hồ sơ')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <Layout><p>Đang tải...</p></Layout>

  return (
    <Layout>
      <Link to={isEdit ? `/can-bo/${id}` : '/'}>← Quay lại</Link>
      <h1 className="page-title" style={{ marginTop: 12 }}>{isEdit ? 'Sửa hồ sơ' : 'Thêm hồ sơ mới'}</h1>

      <form onSubmit={handleSubmit}>
        <div className="card">
          <Section num="1" title="Thông tin cá nhân">
            <FInput label="Họ và tên khai sinh *" value={form.ho_ten_khai_sinh} onChange={(v) => setField('ho_ten_khai_sinh', v)} required />
            <FInput label="Tên gọi khác" value={form.ten_goi_khac} onChange={(v) => setField('ten_goi_khac', v)} />
            <FSelect label="Giới tính" value={form.gioi_tinh} onChange={(v) => setField('gioi_tinh', v)} options={['', 'Nam', 'Nữ']} />
            <FInput label="Ngày sinh" type="date" value={form.ngay_sinh || ''} onChange={(v) => setField('ngay_sinh', v)} />
            <FInput label="Nơi sinh" value={form.noi_sinh} onChange={(v) => setField('noi_sinh', v)} />
            <FInput label="Số CMND/CCCD" value={form.so_cmnd_cccd} onChange={(v) => setField('so_cmnd_cccd', v)} />
            <FInput label="Quê quán - Xã" value={form.que_quan_xa} onChange={(v) => setField('que_quan_xa', v)} />
            <FInput label="Quê quán - Huyện" value={form.que_quan_huyen} onChange={(v) => setField('que_quan_huyen', v)} />
            <FInput label="Quê quán - Tỉnh" value={form.que_quan_tinh} onChange={(v) => setField('que_quan_tinh', v)} />
            <FInput label="Nơi ở hiện nay" value={form.noi_o_hien_nay} onChange={(v) => setField('noi_o_hien_nay', v)} />
            <FInput label="Điện thoại" value={form.dien_thoai} onChange={(v) => setField('dien_thoai', v)} />
            <FInput label="Email" value={form.email} onChange={(v) => setField('email', v)} />
            <FInput label="Dân tộc" value={form.dan_toc} onChange={(v) => setField('dan_toc', v)} />
            <FInput label="Tôn giáo" value={form.ton_giao} onChange={(v) => setField('ton_giao', v)} />
          </Section>

          <Section title="Đơn vị & trạng thái">
            <FSelect
              label="Đơn vị trực thuộc"
              value={form.don_vi_id}
              onChange={(v) => setField('don_vi_id', v)}
              options={[['', '— Chọn đơn vị —'], ...donViList.map((dv) => [dv.id, dv.ten_don_vi])]}
              keyed
            />
            <FInput label="Số hiệu cán bộ" value={form.so_hieu_can_bo} onChange={(v) => setField('so_hieu_can_bo', v)} />
            <FSelect
              label="Trạng thái"
              value={form.trang_thai}
              onChange={(v) => setField('trang_thai', v)}
              options={['Đang công tác', 'Nghỉ hưu', 'Thôi việc', 'Chuyển công tác']}
            />
          </Section>

          <Section num="4" title="Trình độ, chức vụ, ngạch lương">
            <FInput label="Học hàm/học vị cao nhất" value={form.hoc_ham_hoc_vi_cao_nhat} onChange={(v) => setField('hoc_ham_hoc_vi_cao_nhat', v)} />
            <FSelect
              label="Chức vụ"
              value={form.chuc_vu_id}
              onChange={(v) => setField('chuc_vu_id', v)}
              options={[['', '— Chưa gán chức vụ —'], ...chucVuList.map((cv) => [cv.id, cv.ten_chuc_vu])]}
              keyed
            />
            <FInput label="Lý luận chính trị" value={form.ly_luan_chinh_tri} onChange={(v) => setField('ly_luan_chinh_tri', v)} />
            <FInput label="Ngạch công chức" value={form.ngach_cong_chuc} onChange={(v) => setField('ngach_cong_chuc', v)} />
            <FInput label="Bậc lương" value={form.bac_luong} onChange={(v) => setField('bac_luong', v)} />
            <FInput label="Hệ số lương" type="number" step="0.01" value={form.he_so_luong} onChange={(v) => setField('he_so_luong', v)} />
          </Section>

          <RepeatSection
            num="26"
            title="Đào tạo, bồi dưỡng"
            rows={form.dao_tao}
            onAdd={() => addRow('dao_tao', { ten_truong: '', nganh_hoc: '', tu_nam: '', den_nam: '', hinh_thuc_hoc: '', van_bang_chung_chi: '' })}
            onRemove={(i) => removeRow('dao_tao', i)}
            fields={[
              ['ten_truong', 'Tên trường'], ['nganh_hoc', 'Ngành học'],
              ['tu_nam', 'Từ năm'], ['den_nam', 'Đến năm'],
              ['hinh_thuc_hoc', 'Hình thức'], ['van_bang_chung_chi', 'Văn bằng'],
            ]}
            onChange={(i, field, v) => updateRow('dao_tao', i, field, v)}
          />

          <RepeatSection
            num="27"
            title="Quá trình công tác"
            rows={form.qua_trinh_cong_tac}
            onAdd={() => addRow('qua_trinh_cong_tac', { tu_thang_nam: '', den_thang_nam: '', chuc_danh_don_vi: '' })}
            onRemove={(i) => removeRow('qua_trinh_cong_tac', i)}
            fields={[['tu_thang_nam', 'Từ'], ['den_thang_nam', 'Đến'], ['chuc_danh_don_vi', 'Chức danh, đơn vị']]}
            onChange={(i, field, v) => updateRow('qua_trinh_cong_tac', i, field, v)}
          />

          <RepeatSection
            num="22"
            title="Khen thưởng"
            rows={form.khen_thuong}
            onAdd={() => addRow('khen_thuong', { noi_dung: '', nam: '' })}
            onRemove={(i) => removeRow('khen_thuong', i)}
            fields={[['noi_dung', 'Nội dung'], ['nam', 'Năm']]}
            onChange={(i, field, v) => updateRow('khen_thuong', i, field, v)}
          />

          <RepeatSection
            num="23"
            title="Kỷ luật"
            rows={form.ky_luat}
            onAdd={() => addRow('ky_luat', { hinh_thuc: '', cap_quyet_dinh: '', ly_do: '', nam: '' })}
            onRemove={(i) => removeRow('ky_luat', i)}
            fields={[['hinh_thuc', 'Hình thức'], ['cap_quyet_dinh', 'Cấp QĐ'], ['ly_do', 'Lý do'], ['nam', 'Năm']]}
            onChange={(i, field, v) => updateRow('ky_luat', i, field, v)}
          />

          <RepeatSection
            num="30"
            title="Quan hệ gia đình"
            rows={form.quan_he_gia_dinh}
            onAdd={() => addRow('quan_he_gia_dinh', { nhom: 'Bản thân', quan_he: '', ho_ten: '', nam_sinh: '', thong_tin: '' })}
            onRemove={(i) => removeRow('quan_he_gia_dinh', i)}
            fields={[['nhom', 'Nhóm'], ['quan_he', 'Quan hệ'], ['ho_ten', 'Họ tên'], ['nam_sinh', 'Năm sinh'], ['thong_tin', 'Thông tin']]}
            onChange={(i, field, v) => updateRow('quan_he_gia_dinh', i, field, v)}
          />
        </div>

        {error && <p className="flash error" style={{ marginTop: 16 }}>{error}</p>}

        <div style={{ marginTop: 20 }}>
          <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Đang lưu...' : (isEdit ? 'Lưu thay đổi' : 'Thêm hồ sơ')}</button>
        </div>
      </form>
    </Layout>
  )
}

// ---- component phụ ----
function Section({ num, title, children }) {
  return (
    <>
      <div className="section-title">{num && <span className="section-num">{num}</span>} {title}</div>
      <div className="form-grid cols-3">{children}</div>
    </>
  )
}

function FInput({ label, value, onChange, type = 'text', required, step, span }) {
  return (
    <div className={`f-group ${span ? `span-${span}` : ''}`}>
      <label>{label}</label>
      <input
        type={type}
        step={step}
        value={value ?? ''}
        required={required}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  )
}

function FSelect({ label, value, onChange, options, keyed = false, span }) {
  return (
    <div className={`f-group ${span ? `span-${span}` : ''}`}>
      <label>{label}</label>
      <select value={value ?? ''} onChange={(e) => onChange(e.target.value)}>
        {options.map((opt) =>
          keyed
            ? <option key={opt[0]} value={opt[0]}>{opt[1]}</option>
            : <option key={opt} value={opt}>{opt || '—'}</option>
        )}
      </select>
    </div>
  )
}

function RepeatSection({ num, title, rows, fields, onAdd, onRemove, onChange }) {
  return (
    <>
      <div className="section-title">{num && <span className="section-num">{num}</span>} {title}</div>
      <table className="repeat-table">
        <thead>
          <tr>{fields.map(([, label]) => <th key={label}>{label}</th>)}<th></th></tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {fields.map(([key]) => (
                <td key={key}>
                  <input
                    value={row[key] ?? ''}
                    onChange={(e) => onChange(i, key, e.target.value)}
                  />
                </td>
              ))}
              <td><button type="button" className="btn btn-outline btn-sm" onClick={() => onRemove(i)}>✕</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="repeat-actions">
        <button type="button" className="btn btn-outline btn-sm" onClick={onAdd}>+ Thêm dòng</button>
      </div>
    </>
  )
}
