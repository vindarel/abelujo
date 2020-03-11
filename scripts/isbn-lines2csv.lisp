(defun isbn-lines2csv (txtfilename newcsvname)
  "When a txt file contains one ISBN by line, create a csv with 1 quantity.

  Usage:

  (isbn-lines2csv "arbre-lelivrejeunesse.txt" "arbre-lelivrejeunesse.csv")
  "
  (for-file-lines (txtfilename)
                  (with-fields ((isbn))
                    (with-open-file (f newcsvname
                                       :direction :output
                                       :if-exists :append
                                       :if-does-not-exist :create)

                      (write-sequence (format nil "~a;1~&" isbn) f))))
  t)
