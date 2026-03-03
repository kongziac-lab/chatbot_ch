import type { Category, Translations } from '@/types';

export const categories: Category[] = [
  {
    id: 'admission',
    label: { ko: '입학/졸업', zh: '入学/毕业' },
    color: 'from-blue-500 to-blue-600',
    icon: 'GraduationCap',
    subCategories: [
      { id: 'admission-1', label: { ko: '입학전형', zh: '入学考试' } },
      { id: 'admission-2', label: { ko: '입학원서', zh: '入学申请' } },
      { id: 'admission-3', label: { ko: '졸업이수', zh: '毕业学分' } },
      { id: 'admission-4', label: { ko: '도착보고', zh: '到达报告' } },
    ],
  },
  {
    id: 'academic',
    label: { ko: '학사/수업', zh: '学士/课程' },
    color: 'from-emerald-500 to-emerald-600',
    icon: 'BookOpen',
    subCategories: [
      { id: 'academic-1', label: { ko: '수강신청', zh: '选课申请' } },
      { id: 'academic-2', label: { ko: '성적관련', zh: '成绩相关' } },
      { id: 'academic-3', label: { ko: '학적변동', zh: '学籍变动' } },
      { id: 'academic-4', label: { ko: '학생등록', zh: '学生注册' } },
      { id: 'academic-5', label: { ko: '장학금', zh: '奖学金' } },
      { id: 'academic-6', label: { ko: '출결처리', zh: '出勤处理' } },
    ],
  },
  {
    id: 'visa',
    label: { ko: '비자/체류/비교과', zh: '签证/滞留/比较课外' },
    color: 'from-amber-500 to-amber-600',
    icon: 'FileText',
    subCategories: [
      { id: 'visa-1', label: { ko: '비자관련', zh: '签证相关' } },
      { id: 'visa-2', label: { ko: '체류관련', zh: '滞留相关' } },
      { id: 'visa-3', label: { ko: '외국인등록증', zh: '外国人登录证' } },
      { id: 'visa-4', label: { ko: '비교과프로그램', zh: '比较课外项目' } },
    ],
  },
  {
    id: 'life',
    label: { ko: '생활/숙박', zh: '生活/住宿' },
    color: 'from-rose-500 to-rose-600',
    icon: 'Home',
    subCategories: [
      { id: 'life-1', label: { ko: '기숙사', zh: '宿舍' } },
      { id: 'life-2', label: { ko: '보험생활', zh: '保险生活' } },
      { id: 'life-3', label: { ko: '아르바이트', zh: '兼职打工' } },
      { id: 'life-4', label: { ko: '질병건강', zh: '疾病健康' } },
      { id: 'life-5', label: { ko: '은행카드', zh: '银行卡' } },
      { id: 'life-6', label: { ko: '운전면허증', zh: '驾驶证' } },
      { id: 'life-7', label: { ko: '휴대폰', zh: '手机' } },
      { id: 'life-8', label: { ko: '도착보고', zh: '到达报告' } },
      { id: 'life-9', label: { ko: '방학생활', zh: '假期生活' } },
    ],
  },
];

export const translations: Translations = {
  welcome: {
    ko: '계명대학교에 오신 것을 환영합니다',
    zh: '欢迎来到启明大学',
  },
  subtitle: {
    ko: '장춘대학 계명학원 학생을 위한 채팅 도우미',
    zh: '长春大学启明学院学生聊天助手',
  },
  selectLanguage: {
    ko: '언어를 선택해주세요',
    zh: '请选择语言',
  },
  start: {
    ko: '시작하기',
    zh: '开始',
  },
  botTitle: {
    ko: '계명AI봇',
    zh: '启明AI机器人',
  },
  botWelcome: {
    ko: "안녕하세요. '계명AI봇'은 계명대학교에서의 유학생활에 관하여 궁금한 사항을 문의하시면 답변해 드리는 인공지능 상담사입니다.",
    zh: "您好。'启明AI机器人'是为在启明大学的留学生活中有疑问时提供解答的人工智能咨询员。",
  },
  instruction1: {
    ko: '① 아래 메뉴에서 선택해 주시거나',
    zh: '① 请从下方菜单中选择，或',
  },
  instruction2: {
    ko: "② '챗봇에게 메시지 보내기'란에 직접 질의어를 입력해 주세요 (예: 입학 신청 자료)",
    zh: "② 在'向聊天机器人发送消息'栏中直接输入查询词（例如：入学申请资料）",
  },
  placeholder: {
    ko: '챗봇에게 메시지 입력...',
    zh: '输入消息给聊天机器人...',
  },
  send: {
    ko: '전송',
    zh: '发送',
  },
  back: {
    ko: '뒤로가기',
    zh: '返回',
  },
  mainMenu: {
    ko: '메인 메뉴',
    zh: '主菜单',
  },
  selectOption: {
    ko: '원하시는 항목을 선택해주세요',
    zh: '请选择您想要的选项',
  },
  korean: {
    ko: '한국어',
    zh: '韩语',
  },
  chinese: {
    ko: '中文',
    zh: '中文',
  },
};
