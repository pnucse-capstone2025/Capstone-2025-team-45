import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { useTheme } from '@emotion/react';

const CommonCard = ({ title, header, children, footer, ...rest }) => {
  const theme = useTheme();

  return (
    <Card
      elevation={1}
      sx={{
        backgroundColor: theme.palette.background.white,
        color: theme.palette.text.black,
        borderRadius: theme.shape.borderRadius,
        border: `1px solid ${theme.palette.divider}`,
        boxShadow: theme.shadows[1],
      }}
      {...rest} // 사용자 정의 속성 허용
    >
      <CardContent>
        {/* 헤더 영역 */}
        {header && <Box mb={2}>{header}</Box>}

        {/* 타이틀 */}
        {typeof title === 'string' ? (
          <Typography
            variant="h6"
            fontWeight="bold"
            gutterBottom
            align="center"
            sx={{ color: theme.palette.text.black }}
          >
            {title}
          </Typography>
        ) : (
          title // JSX 요소로도 허용
        )}

        {children && <Box mt={1}>{children}</Box>}
        {footer && <Box mt={2}>{footer}</Box>}
      </CardContent>
    </Card>
  );
};

export default CommonCard;