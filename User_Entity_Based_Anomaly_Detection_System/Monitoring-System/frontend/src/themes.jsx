import { createTheme } from '@mui/material/styles';
import '@fontsource/outfit';

const colors = {
  blue: {
    100: '#cce7f4',
    200: '#99cfe9',
    300: '#66b8dd',
    400: '#33a0d2',
    500: '#0088c7',
    600: '#006d9f',
    700: '#005277',
    800: '#003650',
    900: '#001b28',
  },
  gery: {
    100: '#d0d1d5',
    200: '#a1a4ab',
    300: '#727681',
    400: '#434957',
    500: '#141b2d',
    600: '#101624',
    700: '#0c101b',
    800: '#080b12',
    900: '#040509',
  },
  green: {
    100: '#dbf5ee',
    200: '#b7ebde',
    300: '#94e2cd',
    400: '#70d8bd',
    500: '#16A34A',
    600: '#3da58a',
    700: '#2e7c67',
    800: '#1e5245',
    900: '#0f2922',
  },
  indigo: {
    100: '#e1e2fe',
    200: '#c3c6fd',
    300: '#a4a9fc',
    400: '#868dfb',
    500: '#6870fa',
    600: '#535ac8',
    700: '#3e4396',
    800: '#2a2d64',
    900: '#151632',
  },
  orange: {
    100: '#fdecce',
    200: '#fbd89d',
    300: '#f9c56d',
    400: '#f7b13c',
    500: '#f59e0b',
    600: '#c47e09',
    700: '#935f07',
    800: '#623f04',
    900: '#312002',
  },
  red: {
    100: '#fcdada',
    200: '#f9b4b4',
    300: '#f58f8f',
    400: '#f26969',
    500: '#ef4444',
    600: '#bf3636',
    700: '#8f2929',
    800: '#601b1b',
    900: '#300e0e',
  },
  white: {
    100: '#ffffff',
  },
  black: {
    100: '#000000',
  }
};
const theme = createTheme({
  palette: {
    mode: 'dark',

    primary: {
      main: '#0f0f0f',       // 거의 블랙에 가까운 딥그레이
      light: '#1a1a1a',
      dark: '#000000',
      white: '#ffffff',
    },
    secondary: {
      main: '#3b3b3b',       // 어두운 회색 포인트
      dark: '#2a2a2a',
      light: '#4a4a4a',
    },
    background: {
      default: '#121212',    // 전체 배경
      paper: '#1e1e1e',      // 카드, 박스 등
      white: '#ffffff', // 흰색 배경 (필요시 사용)
    },
    text: {
      primary: '#e4e4e7',    // 밝은 회색 글자
      secondary: '#a1a1aa',  // 중간 회색
      disabled: '#52525b',   // 흐릿한 회색
      black: '#000000',      // 검정색 글자
    },
    divider: '#2e2e2e',       // 테두리/구분선
    error: {
      main: '#ef4444',       // 기존 유지
    },
    warning: {
      main: '#f59e0b',
    },
    success: {
      main: '#16A34A',
    },
    info: {
      main: '#3b82f6',
    },
    // 선택 사항: 커스텀 컬러
    grey: {
      100: '#f4f4f5',
      200: '#e4e4e7',
      300: '#d4d4d8',
      400: '#a1a1aa',
      500: '#71717a',
      600: '#52525b',
      700: '#3f3f46',
      800: '#27272a',
      900: '#18181b',
    },
  },
  typography: {
    fontFamily: ['Outfit', 'Roboto', 'sans-serif'].join(','),
    fontWeightLight: 300,
    fontWeightRegular: 400,
    fontWeightMedium: 500,
    fontWeightBold: 700,
  },
  shape: {
    borderRadius: 1,
  },
  components: {
    MuiTableCell: {
      styleOverrides: {
        root: {
          textAlign: 'center',
          color: '#e2e8f0', // 테이블 셀 폰트 색상
        },
        head: {
          fontWeight: 'bold',
          backgroundColor: '#1e293b',
          color: '#f1f5f9',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          input: {
            color: '#000000ff',  // 입력 글자 색
          },
          label: {
            color: '#a1a1aa', // 라벨 색
          }
        }
      }
    },
    MuiInputBase: {
      styleOverrides: {
        input: {
          color: '#e4e4e7',
        }
      }
    }
  },
});
export default theme;
