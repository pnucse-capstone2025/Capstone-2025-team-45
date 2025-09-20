import theme from '../../../themes.jsx';

const Footer = () => {
    return (
        <div
            className="flex justify-center w-full items-center h-10 border-t border-gray-400"
            style={{ backgroundColor: theme.palette.secondary.main }}
        >
            <div className="flex w-full items-center px-4">
                <div className="text-xs text-white">
                    Copyright ⓒ 제로트러스트 클라우드 보안 연구센터. All Rights Reserved.
                </div>
            </div>
        </div>
    );
};

export default Footer;
