"use client";

import React, { useState } from "react";

import {
  mdiClipboardCheckOutline,
  mdiClipboardOutline,
  mdiClose,
  mdiTextBoxPlus,
} from "@mdi/js";
import Icon from "@mdi/react";

import styles from "../styles/FullContentModal.module.css";

import { Button, Modal } from "react-bootstrap";

interface ModalProps {
  content: string;
  header: string;
}

const FullContentModal: React.FC<ModalProps> = ({ header, content }) => {
  const [show, setShow] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  const handleClose = () => {
    setShow(false);
  };
  const handleShow = () => {
    setShow(true);
  };

  const copyToClipboard = () => {
    navigator.clipboard
      .writeText(content)
      .then(() => {
        setIsCopied(true);
        setTimeout(() => {
          setIsCopied(false);
        }, 2000);
      })
      .catch((err) => {
        alert(`Failed to copy text: ${err}`);
      });
  };

  return (
    <>
      <Button onClick={handleShow} className={styles.buttonShowModal}>
        <Icon
          path={mdiTextBoxPlus}
          size={0.825}
          className={styles.iconShowModal}
        />
      </Button>
      <Modal show={show} onHide={handleClose} centered size="xl">
        <Modal.Header className={styles.modalHeader}>
          <Modal.Title>
            <code>{header}</code>
          </Modal.Title>
          <div className={styles.spacer}></div>
          <Button onClick={copyToClipboard} className={styles.button}>
            <Icon
              path={isCopied ? mdiClipboardCheckOutline : mdiClipboardOutline}
              size={1}
              className={styles.icon}
            />
          </Button>
          <Button onClick={handleClose} className={styles.button}>
            <Icon path={mdiClose} size={1} className={styles.icon} />
          </Button>
        </Modal.Header>
        <Modal.Body className={styles.modalBody}>
          <pre className={styles.content}>
            {content.split("\n").map((line, index) => (
              <div key={index} className={styles.line}>
                <span
                  className={`${styles.lineNumber} ${
                    index === 0 ? styles.firstLine : ""
                  }`}
                >
                  {index + 1}
                </span>
                <code
                  className={`${styles.code} ${
                    index === 0 ? styles.firstLine : ""
                  }`}
                >
                  {line}
                </code>
              </div>
            ))}
          </pre>
        </Modal.Body>
      </Modal>
    </>
  );
};

export default FullContentModal;
