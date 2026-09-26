export type BusinessGroup = {
  key: string;
  title: string;
  description: string;
  modules: string[];
};

export const businessGroups: BusinessGroup[] = [
  {
    key: 'overview',
    title: 'Điều hành dự án',
    description: 'Dự án, WBS, công việc, tiến độ và nguồn lực.',
    modules: ['projects', 'tasks', 'schedule', 'resources']
  },
  {
    key: 'commercial',
    title: 'Chi phí & hợp đồng',
    description: 'BOQ, ngân sách, thanh toán, hợp đồng, mua sắm và phát sinh.',
    modules: ['costs', 'contracts', 'changes']
  },
  {
    key: 'documents',
    title: 'Hồ sơ & chất lượng',
    description: 'Document Control, bản vẽ, RFI/NCR/INS, nghiệm thu và kiểm định.',
    modules: ['documents', 'quality']
  },
  {
    key: 'control',
    title: 'Phối hợp & kiểm soát',
    description: 'Trao đổi, dashboard, workflow, cảnh báo và AI.',
    modules: ['collaboration', 'dashboard', 'automation']
  }
];

export const statusLabels: Record<string, string> = {
  planning: 'Chuẩn bị',
  active: 'Đang thực hiện',
  on_hold: 'Tạm dừng',
  completed: 'Hoàn thành',
  closed: 'Đóng',
  cancelled: 'Hủy',
  expired: 'Hết hiệu lực',
  draft: 'Soạn thảo',
  submitted: 'Đã trình',
  under_review: 'Đang duyệt',
  approved: 'Đã phê duyệt',
  rejected: 'Yêu cầu chỉnh sửa',
  paid: 'Đã thanh toán',
  requested: 'Đề nghị',
  ordered: 'Đã đặt hàng',
  delivered: 'Đã giao',
  sent: 'Đã gửi',
  received: 'Đã nhận',
  open: 'Mở',
  todo: 'Chưa bắt đầu',
  in_progress: 'Đang thực hiện',
  review: 'Chờ kiểm tra',
  done: 'Hoàn thành',
  inactive: 'Ngưng sử dụng',
  low: 'Thấp',
  medium: 'Trung bình',
  high: 'Cao',
  critical: 'Khẩn',
  actual: 'Thực tế',
  commitment: 'Cam kết',
  forecast: 'Dự báo',
  cost: 'Chi phí',
  time: 'Thời gian',
  cost_time: 'Chi phí + thời gian'
};

export const documentTypeLabels: Record<string, string> = {
  RFA: 'RFA - Hồ sơ trình duyệt',
  RFI: 'RFI - Yêu cầu thông tin',
  BBHT: 'Biên bản hiện trường',
  NKCT: 'Nhật ký công trường',
  NTCV: 'Nghiệm thu công việc',
  NTVL: 'Nghiệm thu vật liệu đầu vào',
  KDVT: 'Kiểm định vật tư',
  BBHOP: 'Biên bản họp',
  SHOPDRAWING: 'Shopdrawing',
  ISSUED_DESIGN: 'Bản vẽ phát hành TKTC',
  UPDATED: 'Bản vẽ cập nhật',
  AS_BUILT: 'Bản vẽ hoàn công',
  GENERAL: 'Hồ sơ khác'
};

export const qualityTypeLabels: Record<string, string> = {
  NCR: 'NCR - Không phù hợp',
  RFI: 'RFI - Yêu cầu thông tin',
  INS: 'INS - Yêu cầu nghiệm thu',
  NTCV: 'Nghiệm thu công việc',
  NTVL: 'Nghiệm thu vật liệu đầu vào',
  KDVT: 'Kiểm định vật tư',
  MATERIAL: 'Phê duyệt vật liệu',
  TEST: 'Thí nghiệm / kiểm định',
  WORK_INSPECTION: 'Kiểm tra công việc'
};

export const productionReference = {
  documentStatuses: {
    NCR: ['Mở', 'Đang khắc phục', 'Chờ kiểm tra', 'Đóng', 'Hủy'],
    RFA: ['Soạn thảo', 'Đã gửi', 'Chờ duyệt', 'Đã duyệt', 'Từ chối', 'Đóng'],
    RFI: ['Đã gửi', 'Chờ phản hồi', 'Đã phản hồi', 'Đóng', 'Hủy'],
    NTCV: ['Chuẩn bị hồ sơ', 'Đã trình nghiệm thu', 'Chờ nghiệm thu', 'Yêu cầu sửa', 'Đạt', 'Không đạt', 'Đóng'],
    NTVL: ['Chuẩn bị hồ sơ', 'Đã trình', 'Chờ kiểm tra', 'Yêu cầu bổ sung', 'Chấp thuận', 'Chấp thuận có điều kiện', 'Không chấp thuận', 'Đóng'],
    KDVT: ['Chuẩn bị hồ sơ', 'Đã gửi kiểm định', 'Đang kiểm định', 'Chờ kết quả', 'Đạt', 'Không đạt', 'Đóng']
  },
  taskStatuses: ['Chưa bắt đầu', 'Đúng tiến độ', 'Nhanh tiến độ', 'Chậm tiến độ', 'Hoàn thành', 'Đang thực hiện', 'Chưa xác định'],
  drawingStatuses: ['Mới nhận', 'Đang kiểm tra', 'Chờ phản hồi', 'Chấp thuận', 'Chấp thuận có điều kiện', 'Cần sửa', 'Thay thế', 'Hủy']
};

export function displayLabel(value: unknown, labels?: Record<string, string>) {
  const text = String(value ?? '');
  return labels?.[text] || statusLabels[text] || documentTypeLabels[text] || qualityTypeLabels[text] || text;
}
