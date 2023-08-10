import React from 'react';
import Sidebar from './Sidebar';
import styles from '../styles/layout.module.css'

interface LayoutProps {
    children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
    return (
        <div className={styles.container}>
            <Sidebar />
            <div className={styles.content}>
                {children}
            </div>
        </div>
    );
}

export default Layout;
