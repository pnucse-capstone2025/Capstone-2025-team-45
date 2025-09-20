import React from 'react';
import PropTypes from 'prop-types';
import { Dialog, DialogTitle, DialogActions, Button } from '@mui/material';

const SessionExpiredAlert = ({ onConfirm }) => {
  return (
    <Dialog open onClose={onConfirm}>
      <DialogTitle>세션이 만료되었습니다. 다시 로그인해주세요.</DialogTitle>
      <DialogActions>
        <Button onClick={onConfirm} color="primary" autoFocus>
          확인
        </Button>
      </DialogActions>
    </Dialog>
  );
};

SessionExpiredAlert.propTypes = {
  onConfirm: PropTypes.func.isRequired,
};

export default SessionExpiredAlert;
