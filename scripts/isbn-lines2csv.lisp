(defun isbn-lines2csv (txtfilename newcsvname)
  "When a txt file contains one ISBN by line, create a csv with 1 quantity.

  Usage:

  (isbn-lines2csv \"arbre-lelivrejeunesse.txt\" \"arbre-lelivrejeunesse.csv\")
  "
  (for-file-lines (txtfilename)
                  (with-fields ((isbn))
                    (with-open-file (f newcsvname
                                       :direction :output
                                       :if-exists :append
                                       :if-does-not-exist :create)

                      ;TODO: count occurences.
                      ;like
                      ;grep "\S" DEPOT\ CUISINE.TXT   | sort | uniq -c | sort -r | awk '{print $2 ";" $1}' > depot-cuisine.csv
                      (write-sequence (format nil "~a;1~&" isbn) f))))
  t)

(defun isbn-minus-one-quantity ()
  (let ((*fs* ";"))
    (with-open-file (f #p"inventaire2021-full-minus.csv"
                       :direction :output
                       :if-exists :supersede
                       :if-does-not-exist :create)
      (for-file-lines (#p"inventaire2021-full.csv")
                      (with-fields ((isbn qty))
                        (format f "~a;~a~&" isbn (clawk:$- qty 1)))))))
