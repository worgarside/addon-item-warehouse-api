"use client";

import React, { useRef, useState, useEffect } from "react";

import styles from "../styles/Cell.module.css";

import FullContentModal from "./FullContentModal.client";

const Cell: React.FC<{ content: string; header: string }> = ({
  content,
  header,
}) => {
  const [isOverflowing, setIsOverflowing] = useState(false);
  const cellRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (cellRef.current) {
      const element = cellRef.current;
      if (element.scrollHeight > element.clientHeight) {
        setIsOverflowing(true);
      }
    }
  }, []);

  return (
    <td key={header} className={styles.cell}>
      <div className={styles.cellInner} ref={cellRef}>
        {isOverflowing ? (
          <>
            <div className={styles.scrollable}>
              <pre>
                <code>{content}</code>
              </pre>
            </div>
            <FullContentModal content={content} header={header} />
          </>
        ) : (
          <code>{content}</code>
        )}
      </div>
    </td>
  );
};

export default Cell;
